/// Domain repository for step sync — reference: BottomNavbarRepository.setStepsAndPoints.
abstract class StepsRepository {
  /// Upsert today's step count; returns API payload including points_awarded.
  Future<Map<String, dynamic>> syncDailySteps({
    required String date,
    required int stepCount,
  });
}
