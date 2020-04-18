// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'main.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

StItem _$StItemFromJson(Map<String, dynamic> json) {
  return StItem(
      json['name'] as String, json['alertFlag'] as bool, json['v'] as String);
}

Map<String, dynamic> _$StItemToJson(StItem instance) => <String, dynamic>{
      'name': instance.name,
      'alertFlag': instance.alertFlag,
      'v': instance.v
    };

StGroup _$StGroupFromJson(Map<String, dynamic> json) {
  return StGroup(
      json['name'] as String,
      (json['items'] as List)
          ?.map((e) =>
              e == null ? null : StItem.fromJson(e as Map<String, dynamic>))
          ?.toList());
}

Map<String, dynamic> _$StGroupToJson(StGroup instance) => <String, dynamic>{
      'name': instance.name,
      'items': instance.items?.map((e) => e?.toJson())?.toList()
    };

StServer _$StServerFromJson(Map<String, dynamic> json) {
  return StServer(
      json['name'] as String,
      (json['items'] as List)
          ?.map((e) =>
              e == null ? null : StItem.fromJson(e as Map<String, dynamic>))
          ?.toList(),
      (json['groups'] as List)
          ?.map((e) =>
              e == null ? null : StGroup.fromJson(e as Map<String, dynamic>))
          ?.toList());
}

Map<String, dynamic> _$StServerToJson(StServer instance) => <String, dynamic>{
      'name': instance.name,
      'items': instance.items?.map((e) => e?.toJson())?.toList(),
      'groups': instance.groups?.map((e) => e?.toJson())?.toList()
    };
