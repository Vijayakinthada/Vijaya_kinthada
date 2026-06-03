import 'package:shared_preferences/shared_preferences.dart';

class UserScope {
  const UserScope({
    required this.userId,
    required this.profileId,
    this.tenantId,
    required this.displayName,
  });

  final String userId;
  final String profileId;
  final String? tenantId;
  final String displayName;

  Map<String, String> toHeaders() => {
        'X-User-Id': userId,
        'X-Profile-Id': profileId,
        if (tenantId != null) 'X-Tenant-Id': tenantId!,
      };

  factory UserScope.fromJson(Map<String, dynamic> json) => UserScope(
        userId: json['user_id'] as String,
        profileId: json['profile_id'] as String,
        tenantId: json['tenant_id'] as String?,
        displayName: json['display_name'] as String,
      );
}

class ScopeStorage {
  static const _key = 'gentle_activity_scope';

  static Future<void> save(UserScope scope) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setStringList(_key, [
      scope.userId,
      scope.profileId,
      scope.tenantId ?? '',
      scope.displayName,
    ]);
  }

  static Future<UserScope?> load() async {
    final prefs = await SharedPreferences.getInstance();
    final data = prefs.getStringList(_key);
    if (data == null || data.length < 4) return null;
    return UserScope(
      userId: data[0],
      profileId: data[1],
      tenantId: data[2].isEmpty ? null : data[2],
      displayName: data[3],
    );
  }

  static Future<void> clear() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_key);
  }
}
