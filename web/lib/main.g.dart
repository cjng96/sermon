// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'main.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

StLoadAvg _$StLoadAvgFromJson(Map<String, dynamic> json) {
  return StLoadAvg()
    ..cnt = json['cnt'] as int
    ..avg = (json['avg'] as List)?.map((e) => (e as num)?.toDouble())?.toList();
}

Map<String, dynamic> _$StLoadAvgToJson(StLoadAvg instance) =>
    <String, dynamic>{'cnt': instance.cnt, 'avg': instance.avg};

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
    ..total = json['total'] as int
    ..percent = (json['percent'] as num)?.toDouble();
}

Map<String, dynamic> _$StMemToJson(StMem instance) =>
    <String, dynamic>{'total': instance.total, 'percent': instance.percent};

StSwap _$StSwapFromJson(Map<String, dynamic> json) {
  return StSwap()
    ..total = json['total'] as int
    ..percent = (json['percent'] as num)?.toDouble();
}

Map<String, dynamic> _$StSwapToJson(StSwap instance) =>
    <String, dynamic>{'total': instance.total, 'percent': instance.percent};

StStatus _$StStatusFromJson(Map<String, dynamic> json) {
  return StStatus()
    ..cpu = (json['cpu'] as num)?.toDouble()
    ..load = json['load'] == null
        ? null
        : StLoadAvg.fromJson(json['load'] as Map<String, dynamic>)
    ..disk = json['disk'] == null
        ? null
        : StDisk.fromJson(json['disk'] as Map<String, dynamic>)
    ..mem = json['mem'] == null
        ? null
        : StMem.fromJson(json['mem'] as Map<String, dynamic>)
    ..swap = json['swap'] == null
        ? null
        : StSwap.fromJson(json['swap'] as Map<String, dynamic>)
    ..apps = json['apps'] as Map<String, dynamic>;
}

Map<String, dynamic> _$StStatusToJson(StStatus instance) => <String, dynamic>{
      'cpu': instance.cpu,
      'load': instance.load?.toJson(),
      'disk': instance.disk?.toJson(),
      'mem': instance.mem?.toJson(),
      'swap': instance.swap?.toJson(),
      'apps': instance.apps
    };

Server _$ServerFromJson(Map<String, dynamic> json) {
  return Server()
    ..name = json['name'] as String
    ..status = json['status'] == null
        ? null
        : StStatus.fromJson(json['status'] as Map<String, dynamic>);
}

Map<String, dynamic> _$ServerToJson(Server instance) => <String, dynamic>{
      'name': instance.name,
      'status': instance.status?.toJson()
    };
