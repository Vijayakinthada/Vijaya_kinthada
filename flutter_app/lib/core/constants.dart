const String wellnessDisclaimer =
    'For general wellness only — not a substitute for professional medical care.';

const String apiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://localhost:8000',
);

const List<String> gentleSessionTypes = [
  'walking',
  'light_stretching',
  'gentle_mobility',
  'breathing_walk',
];
