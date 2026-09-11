import 'dart:convert';
import 'dart:io';

import 'package:path_provider/path_provider.dart';

class AccountSession {
  AccountSession({
    required this.token,
    required this.farmerId,
    required this.email,
    this.name = '',
    this.address,
    this.jurisdictionId = 'tembalang',
    this.isActive = true,
  });

  final String token;
  final String farmerId;
  final String email;
  final String name;
  final String? address;
  final String jurisdictionId;
  final bool isActive;

  Map<String, dynamic> toJson() => {
    'token': token,
    'farmer_id': farmerId,
    'email': email,
    'name': name,
    'address': address,
    'jurisdiction_id': jurisdictionId,
    'is_active': isActive,
  };

  factory AccountSession.fromJson(Map<String, dynamic> json) => AccountSession(
    token: json['token'] as String? ?? '',
    farmerId:
        (json['farmer_id'] ?? json['farmerId'] ?? json['id']) as String? ?? '',
    email: json['email'] as String? ?? '',
    name: json['name'] as String? ?? '',
    address: json['address'] as String?,
    jurisdictionId:
        (json['jurisdiction_id'] ?? json['jurisdictionId']) as String? ??
        'tembalang',
    isActive: json['is_active'] as bool? ?? true,
  );

  AccountSession copyWith({
    String? name,
    String? address,
    bool clearAddress = false,
    String? jurisdictionId,
    bool? isActive,
  }) => AccountSession(
    token: token,
    farmerId: farmerId,
    email: email,
    name: name ?? this.name,
    address: clearAddress ? null : address ?? this.address,
    jurisdictionId: jurisdictionId ?? this.jurisdictionId,
    isActive: isActive ?? this.isActive,
  );
}

class FarmerRegistrationDraft {
  FarmerRegistrationDraft({
    required this.name,
    required this.email,
    required this.password,
    required this.jurisdictionId,
    this.address,
  });
  final String name;
  final String email;
  final String password;
  final String jurisdictionId;
  final String? address;

  Map<String, dynamic> toJson() => {
    'name': name,
    'email': email,
    'password': password,
    'jurisdiction_id': jurisdictionId,
    'address': address,
  };
}

class FarmerProfileDraft {
  FarmerProfileDraft({
    required this.name,
    required this.jurisdictionId,
    this.address,
  });
  final String name;
  final String jurisdictionId;
  final String? address;
  Map<String, dynamic> toJson() => {
    'name': name,
    'jurisdiction_id': jurisdictionId,
    'address': address,
  };
}

abstract class SessionStore {
  Future<void> save(AccountSession session);
  Future<AccountSession?> load();
  Future<void> clear();
}

class MemorySessionStore implements SessionStore {
  MemorySessionStore({
    this.ttl = const Duration(days: 7),
    AccountSession? initialSession,
    DateTime? initialSavedAt,
  }) {
    if (initialSession != null) {
      _session = initialSession;
      _savedAt = initialSavedAt ?? DateTime.now();
    }
  }

  final Duration ttl;
  AccountSession? _session;
  DateTime? _savedAt;

  String? get token => _session?.token;

  @override
  Future<AccountSession?> load() async {
    if (_session == null) return null;
    if (_savedAt != null && DateTime.now().difference(_savedAt!) > ttl) {
      _session = null;
      _savedAt = null;
      return null;
    }
    return _session;
  }

  @override
  Future<void> save(AccountSession session) async {
    _session = session;
    _savedAt = DateTime.now();
  }

  @override
  Future<void> clear() async {
    _session = null;
    _savedAt = null;
  }
}

class FileSessionStore implements SessionStore {
  FileSessionStore({
    this.fileOverride,
    this.ttl = const Duration(days: 7),
    this.directoryProvider,
  });

  final File? fileOverride;
  final Duration ttl;
  final Future<Directory> Function()? directoryProvider;

  Future<File> _getFile() async {
    if (fileOverride != null) return fileOverride!;
    final dir = await (directoryProvider != null
        ? directoryProvider!()
        : getApplicationDocumentsDirectory());
    return File('${dir.path}/sapisehat_session.json');
  }

  @override
  Future<AccountSession?> load() async {
    try {
      final file = await _getFile();
      if (!await file.exists()) return null;
      final content = await file.readAsString();
      if (content.trim().isEmpty) return null;
      final data = jsonDecode(content) as Map<String, dynamic>;
      final savedAtStr = data['saved_at'] as String?;
      if (savedAtStr == null) {
        await clear();
        return null;
      }
      final savedAt = DateTime.tryParse(savedAtStr);
      if (savedAt == null || DateTime.now().difference(savedAt) > ttl) {
        await clear();
        return null;
      }
      final sessionJson = data['session'] as Map<String, dynamic>?;
      if (sessionJson == null) return null;
      return AccountSession.fromJson(sessionJson);
    } catch (_) {
      return null;
    }
  }

  @override
  Future<void> save(AccountSession session) async {
    try {
      final file = await _getFile();
      await file.parent.create(recursive: true);
      final data = {
        'session': session.toJson(),
        'saved_at': DateTime.now().toIso8601String(),
      };
      await file.writeAsString(jsonEncode(data), flush: true);
    } catch (_) {}
  }

  @override
  Future<void> clear() async {
    try {
      final file = await _getFile();
      if (await file.exists()) {
        await file.delete();
      }
    } catch (_) {}
  }
}
