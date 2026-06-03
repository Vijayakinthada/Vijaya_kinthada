import 'package:dio/dio.dart';

import 'constants.dart';
import 'scope_storage.dart';

class ApiClient {
  ApiClient._(this._dio);

  final Dio _dio;

  static Future<ApiClient> create() async {
    final scope = await ScopeStorage.load();
    final dio = Dio(BaseOptions(
      baseUrl: apiBaseUrl,
      connectTimeout: const Duration(seconds: 10),
      headers: scope?.toHeaders(),
    ));
    dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final current = await ScopeStorage.load();
        if (current != null) {
          options.headers.addAll(current.toHeaders());
        }
        handler.next(options);
      },
    ));
    return ApiClient._(dio);
  }

  Future<Map<String, dynamic>> register({
    required String displayName,
    String? email,
  }) async {
    final resp = await _dio.post('/api/v1/register', data: {
      'display_name': displayName,
      if (email != null) 'email': email,
    });
    return Map<String, dynamic>.from(resp.data as Map);
  }

  Future<Map<String, dynamic>> me() async {
    final resp = await _dio.get('/api/v1/me');
    return Map<String, dynamic>.from(resp.data as Map);
  }

  Future<Map<String, dynamic>> logSession({
    required String sessionType,
    required int durationMinutes,
    required DateTime startedAt,
    String? notes,
  }) async {
    final resp = await _dio.post('/api/v1/sessions', data: {
      'session_type': sessionType,
      'duration_minutes': durationMinutes,
      'started_at': startedAt.toUtc().toIso8601String(),
      if (notes != null) 'notes': notes,
    });
    return Map<String, dynamic>.from(resp.data as Map);
  }

  Future<Map<String, dynamic>> upsertSteps(String date, int stepCount) async {
    final resp = await _dio.put('/api/v1/steps/$date', data: {
      'step_count': stepCount,
    });
    return Map<String, dynamic>.from(resp.data as Map);
  }

  Future<Map<String, dynamic>> upsertGoals({
    required int dailyStepTarget,
    required int dailyActiveMinutesTarget,
  }) async {
    final resp = await _dio.put('/api/v1/goals', data: {
      'daily_step_target': dailyStepTarget,
      'daily_active_minutes_target': dailyActiveMinutesTarget,
    });
    return Map<String, dynamic>.from(resp.data as Map);
  }

  Future<Map<String, dynamic>> upsertReminders({
    required bool enabled,
    String? walkReminderTime,
    String? vitalsReminderTime,
  }) async {
    final resp = await _dio.put('/api/v1/reminders', data: {
      'enabled': enabled,
      if (walkReminderTime != null) 'walk_reminder_time': walkReminderTime,
      if (vitalsReminderTime != null) 'vitals_reminder_time': vitalsReminderTime,
    });
    return Map<String, dynamic>.from(resp.data as Map);
  }

  Future<Map<String, dynamic>> upsertVitals(
    String date, {
    int? bpSystolic,
    int? bpDiastolic,
    int? pulse,
    int? mood,
    double? sleepHours,
    String? notes,
  }) async {
    final resp = await _dio.put('/api/v1/vitals/$date', data: {
      if (bpSystolic != null) 'bp_systolic': bpSystolic,
      if (bpDiastolic != null) 'bp_diastolic': bpDiastolic,
      if (pulse != null) 'pulse': pulse,
      if (mood != null) 'mood': mood,
      if (sleepHours != null) 'sleep_hours': sleepHours,
      if (notes != null) 'notes': notes,
    });
    return Map<String, dynamic>.from(resp.data as Map);
  }

  Future<int> balance() async {
    final resp = await _dio.get('/api/v1/points/balance');
    return (resp.data['balance'] as num).toInt();
  }

  Future<List<dynamic>> ledger() async {
    final resp = await _dio.get('/api/v1/points/ledger');
    return resp.data as List<dynamic>;
  }

  Future<List<dynamic>> history() async {
    final resp = await _dio.get('/api/v1/history');
    return resp.data as List<dynamic>;
  }
}
