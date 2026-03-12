const path = require('path');

function loadGarminConnect() {
  try {
    return require('garmin-connect');
  } catch (primaryError) {
    const appData = process.env.APPDATA;
    if (appData) {
      const globalModulePath = path.join(appData, 'npm', 'node_modules', 'garmin-connect');
      try {
        return require(globalModulePath);
      } catch (secondaryError) {
        throw primaryError;
      }
    }
    throw primaryError;
  }
}

const { GarminConnect } = loadGarminConnect();

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    const current = argv[i];
    if (current === '--start') {
      args.start = argv[i + 1];
      i += 1;
    } else if (current === '--end') {
      args.end = argv[i + 1];
      i += 1;
    }
  }
  return args;
}

function toIsoDate(value) {
  return new Date(value).toISOString().slice(0, 10);
}

function safeNumber(value) {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

async function main() {
  const { start, end } = parseArgs(process.argv.slice(2));
  if (!start || !end) {
    throw new Error('Missing --start or --end argument.');
  }

  const username = process.env.GARMIN_USERNAME;
  const password = process.env.GARMIN_PASSWORD;
  if (!username || !password) {
    throw new Error('GARMIN_USERNAME and GARMIN_PASSWORD are required.');
  }

  const client = new GarminConnect({ username, password });
  await client.login();

  const startDate = new Date(start);
  const endDate = new Date(end);

  const activities = await fetchAllActivities(client);
  const filteredActivities = activities.filter((item) => {
    const dateText = (item.startTimeLocal || item.startTimeGMT || '').slice(0, 10);
    return dateText >= start && dateText <= end;
  });

  const activityRows = filteredActivities.map((item) => ({
    activity_id: String(item.activityId),
    activity_date: (item.startTimeLocal || item.startTimeGMT || '').slice(0, 10),
    start_time: item.startTimeLocal || item.startTimeGMT || null,
    sport: item.activityType?.typeKey || null,
    sub_sport: item.eventType?.typeKey || null,
    duration_minutes: safeNumber(item.duration) != null ? Math.round((item.duration / 60) * 100) / 100 : null,
    distance_km: safeNumber(item.distance) != null ? Math.round((item.distance / 1000) * 100) / 100 : null,
    calories: item.calories ?? null,
    avg_hr: item.averageHR ?? null,
    max_hr: item.maxHR ?? null,
    training_load: item.activityTrainingLoad ?? item.trainingStressScore ?? null,
    avg_speed_kmh: safeNumber(item.averageSpeed) != null ? Math.round((item.averageSpeed * 3.6) * 100) / 100 : null,
  }));

  const activityDetails = filteredActivities.map((item) => ({
    activity_id: String(item.activityId),
    elevation_gain_m: item.elevationGain ?? null,
    avg_cadence: item.averageRunningCadenceInStepsPerMinute ?? item.averageBikingCadenceInRevPerMinute ?? null,
    avg_power: item.avgPower ?? null,
    aerobic_effect: item.aerobicTrainingEffect ?? null,
    anaerobic_effect: item.anaerobicTrainingEffect ?? null,
    detail_json: JSON.stringify(item),
  }));

  const dailySummary = [];
  const sleepRows = [];
  const hrvRows = [];
  const restingHrRows = [];
  const bodyBatteryRows = [];
  const weightRows = [];

  for (let current = new Date(startDate); current <= endDate; current.setDate(current.getDate() + 1)) {
    const currentDate = new Date(current);
    const dateText = toIsoDate(currentDate);

    try {
      const steps = await client.getSteps(currentDate);
      dailySummary.push({
        summary_date: dateText,
        steps: steps ?? 0,
        calories: 0,
        distance_km: 0,
        floors: 0,
        intense_minutes: 0,
        active_kcal: 0,
      });
    } catch {
      dailySummary.push({
        summary_date: dateText,
        steps: 0,
        calories: 0,
        distance_km: 0,
        floors: 0,
        intense_minutes: 0,
        active_kcal: 0,
      });
    }

    try {
      const sleep = await client.getSleepData(currentDate);
      const dto = sleep.dailySleepDTO || {};
      sleepRows.push({
        sleep_date: dateText,
        duration_hours: safeNumber(dto.sleepTimeSeconds) != null ? Math.round((dto.sleepTimeSeconds / 3600) * 100) / 100 : null,
        awake_minutes: safeNumber(dto.awakeSleepSeconds) != null ? Math.round((dto.awakeSleepSeconds / 60) * 100) / 100 : null,
        rem_hours: safeNumber(dto.remSleepSeconds) != null ? Math.round((dto.remSleepSeconds / 3600) * 100) / 100 : null,
        light_hours: safeNumber(dto.lightSleepSeconds) != null ? Math.round((dto.lightSleepSeconds / 3600) * 100) / 100 : null,
        deep_hours: safeNumber(dto.deepSleepSeconds) != null ? Math.round((dto.deepSleepSeconds / 3600) * 100) / 100 : null,
        sleep_score: dto.sleepScores?.overall?.value ?? null,
        bedtime: dto.sleepStartTimestampLocal ?? null,
        wake_time: dto.sleepEndTimestampLocal ?? null,
      });
      hrvRows.push({
        measurement_date: dateText,
        overnight_avg: sleep.avgOvernightHrv ?? null,
        baseline_low: null,
        baseline_high: null,
        hrv_status: sleep.hrvStatus ?? null,
      });
      restingHrRows.push({
        measurement_date: dateText,
        resting_hr_bpm: sleep.restingHeartRate ?? null,
      });

      const bbValues = Array.isArray(sleep.sleepBodyBattery) ? sleep.sleepBodyBattery.map((x) => x.value).filter((x) => typeof x === 'number') : [];
      bodyBatteryRows.push({
        measurement_date: dateText,
        body_battery_max: bbValues.length ? Math.max(...bbValues) : null,
        body_battery_min: bbValues.length ? Math.min(...bbValues) : null,
        body_battery_avg: bbValues.length ? Math.round((bbValues.reduce((a, b) => a + b, 0) / bbValues.length) * 100) / 100 : null,
        end_of_day_value: bbValues.length ? bbValues[bbValues.length - 1] : null,
      });
    } catch {
      sleepRows.push({ sleep_date: dateText });
      hrvRows.push({ measurement_date: dateText });
      restingHrRows.push({ measurement_date: dateText });
      bodyBatteryRows.push({ measurement_date: dateText });
    }

    try {
      const hr = await client.getHeartRate(currentDate);
      const row = restingHrRows.find((item) => item.measurement_date === dateText);
      if (row && row.resting_hr_bpm == null) {
        row.resting_hr_bpm = hr.restingHeartRate ?? null;
      }
    } catch {
    }

    try {
      const weight = await client.getDailyWeightData(currentDate);
      const items = weight.dateWeightList || [];
      const match = items.find((item) => item.calendarDate === dateText);
      if (match) {
        weightRows.push({
          measurement_date: dateText,
          weight_kg: match.weight ?? null,
          body_fat_pct: match.bodyFat ?? null,
          muscle_mass_kg: match.muscleMass ?? null,
          body_water_pct: match.bodyWater ?? null,
          bmi: match.bmi ?? null,
        });
      }
    } catch {
    }
  }

  const output = {
    data: {
      daily_summary: dailySummary,
      sleep: sleepRows,
      hrv: hrvRows,
      resting_hr: restingHrRows,
      body_battery: bodyBatteryRows,
      training_readiness: [],
      training_status: [],
      activities: activityRows,
      activity_details: activityDetails,
      weight_body_composition: weightRows,
    },
  };

  process.stdout.write(JSON.stringify(output));
}

async function fetchAllActivities(client) {
  const pageSize = 100;
  let startIndex = 0;
  const all = [];

  while (true) {
    const chunk = await client.getActivities(startIndex, pageSize);
    if (!Array.isArray(chunk) || chunk.length === 0) {
      break;
    }
    all.push(...chunk);
    if (chunk.length < pageSize) {
      break;
    }
    startIndex += pageSize;
  }

  return all;
}

main().catch((error) => {
  process.stderr.write(String(error && error.stack ? error.stack : error));
  process.exit(1);
});
