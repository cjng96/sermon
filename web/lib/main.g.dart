// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'main.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

StDisk _$StDiskFromJson(Map<String, dynamic> json) {
  return StDisk()
    ..free = json['free'] as int
    ..total = json['total'] as int
    ..used = json['used'] as int;
}

Map<String, dynamic> _$StDiskToJson(StDisk instance) => <String, dynamic>{
      'free': instance.free,
      'total': instance.total,
      'used': instance.used
    };

StMem _$StMemFromJson(Map<String, dynamic> json) {
  return StMem()
    ..free = json['free'] as int
    ..total = json['total'] as int
    ..used = json['used'] as int
    ..percent = (json['percent'] as num)?.toDouble();
}

Map<String, dynamic> _$StMemToJson(StMem instance) => <String, dynamic>{
      'free': instance.free,
      'total': instance.total,
      'used': instance.used,
      'percent': instance.percent
    };

StSystem _$StSystemFromJson(Map<String, dynamic> json) {
  return StSystem()
    ..cpu = (json['cpu'] as num)?.toDouble()
    ..disk = json['disk'] == null
        ? null
        : StDisk.fromJson(json['disk'] as Map<String, dynamic>)
    ..mem = json['mem'] == null
        ? null
        : StMem.fromJson(json['mem'] as Map<String, dynamic>);
}

Map<String, dynamic> _$StSystemToJson(StSystem instance) => <String, dynamic>{
      'cpu': instance.cpu,
      'disk': instance.disk?.toJson(),
      'mem': instance.mem?.toJson()
    };

Server _$ServerFromJson(Map<String, dynamic> json) {
  return Server()
    ..name = json['name'] as String
    ..system = json['system'] == null
        ? null
        : StSystem.fromJson(json['system'] as Map<String, dynamic>);
}

Map<String, dynamic> _$ServerToJson(Server instance) => <String, dynamic>{
      'name': instance.name,
      'system': instance.system?.toJson()
    };
