import '../../../core/api_client.dart';
import 'steps_repository.dart';

/// Data layer — replaces reference Firestore daily steps writes with REST.
class StepsRepositoryImpl implements StepsRepository {
  StepsRepositoryImpl(this._client);

  final ApiClient _client;

  @override
  Future<Map<String, dynamic>> syncDailySteps({
    required String date,
    required int stepCount,
  }) =>
      _client.upsertSteps(date, stepCount);
}
