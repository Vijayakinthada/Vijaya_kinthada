/// Step milestone utilities adapted from Flutter-Steps-Tracker
/// (home_cubit.dart `onFeedbackState`).
///
/// Reference uses `(oldSteps % 100) > (newSteps % 100)` when crossing
/// 100, 200, 300… — equivalent to [crossedHundredStepMilestone].
library;

const int pointsPerHundredSteps = 5;

/// Returns true when [nextSteps] crosses a new 100-step boundary vs [previousSteps].
bool crossedHundredStepMilestone(int previousSteps, int nextSteps) {
  return (previousSteps ~/ 100) < (nextSteps ~/ 100);
}

/// Points earned for reaching [stepCount] (reference: `(steps ~/ 100) * 5`).
int totalPointsForSteps(int stepCount) {
  return (stepCount ~/ 100) * pointsPerHundredSteps;
}

/// Points earned for newly crossed milestones between two counts.
int milestonePointsBetween(int previousSteps, int nextSteps) {
  final prevHundreds = previousSteps ~/ 100;
  final nextHundreds = nextSteps ~/ 100;
  return (nextHundreds - prevHundreds) * pointsPerHundredSteps;
}
