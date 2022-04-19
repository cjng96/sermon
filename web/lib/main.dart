import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';

import 'package:http/http.dart' as http;
import 'package:intl/intl.dart';
import 'package:json_annotation/json_annotation.dart';

void main() => runApp(MyApp());

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Sermon',
      theme: ThemeData(
        primarySwatch: Colors.blue,
      ),
      home: ServerStatusPage(),
    );
  }
}

class ServerStatusPage extends StatefulWidget {
  ServerStatusPage({Key key}) : super(key: key);

  @override
  _ServerStatusPageState createState() => _ServerStatusPageState();
}

class StItem {
  StItem(this.name, this.alertFlag, this.v);
  factory StItem.fromJson(Map<String, dynamic> json) =>
      StItem(json['name'] as String, json['alertFlag'] as bool, json['v'] as String);
  Map<String, dynamic> toJson() => <String, dynamic>{'name': name, 'alertFlag': alertFlag, 'v': v};

  String name;
  bool alertFlag;
  String v;
}

class StGroup {
  StGroup(this.name, this.items);
  factory StGroup.fromJson(Map<String, dynamic> json) => StGroup(json['name'] as String,
      (json['items'] as List)?.map((e) => e == null ? null : StItem.fromJson(e as Map<String, dynamic>))?.toList());
  Map<String, dynamic> toJson() => <String, dynamic>{'name': name, 'items': items?.map((e) => e?.toJson())?.toList()};

  String name;
  List<StItem> items;
}

class StServer {
  StServer(this.name, this.ts, this.items, this.groups);
  factory StServer.fromJson(Map<String, dynamic> json) => StServer(
      json['name'] as String,
      json['ts'] as int,
      (json['items'] as List)?.map((e) => e == null ? null : StItem.fromJson(e as Map<String, dynamic>))?.toList(),
      (json['groups'] as List)?.map((e) => e == null ? null : StGroup.fromJson(e as Map<String, dynamic>))?.toList());

  Map<String, dynamic> toJson() => <String, dynamic>{
        'name': name,
        'ts': ts,
        'items': items?.map((e) => e?.toJson())?.toList(),
        'groups': groups?.map((e) => e?.toJson())?.toList()
      };

  String name;
  int ts;
  List<StItem> items;
  List<StGroup> groups;
}

String duration2str(Duration d) {
  String td(int n) {
    if (n >= 10) return "$n";
    return "0$n";
  }

  String ss = '${td(d.inMinutes.remainder(60))}:${td(d.inSeconds.remainder(60))}';
  if (d.inDays != 0 || d.inHours != 0) {
    ss = '${td(d.inHours)}:' + ss;
    if (d.inDays != 0) {
      ss = '${d.inDays}D ' + ss;
    }
  }

  return ss;
}

class _ServerStatusPageState extends State<ServerStatusPage> {
  List<StServer> servers = [];

  Future<void> _refresh() async {
    try {
      await doStatus();
    } catch (e) {
      print(e);
    }
    setState(() {});
  }

  Future<void> doStatus() async {
    var pk = {'type': 'status'};
    final ss = jsonEncode(pk);

    // var url = 'http://localhost:25090/cmd';
    // if (kReleaseMode) {
    const url = kReleaseMode
        ? String.fromEnvironment('SERVER_URL', defaultValue: 'http://localhost:25090/cmd')
        : 'http://watchmon.ucount.it/cmd';

    final res = await http.post(Uri.parse(url), body: ss).timeout(const Duration(seconds: 30));
    if (res.statusCode != 200) {
      throw Exception('http error code - ${res.statusCode} - [${res.body}]');
    }
    final map = json.decode(res.body) as List<dynamic>;
    print('map - $map');

    List<StServer> newServers = [];
    for (final item in map) {
      newServers.add(StServer.fromJson(item));
    }
    servers = newServers;
    //print('server - $servers');
  }

  void _initCode() async {
    while (true) {
      await _refresh();
      await Future.delayed(Duration(seconds: 5));
    }
  }

  @override
  void initState() {
    super.initState();
    _initCode();
  }

  @override
  Widget build(BuildContext context) {
    Widget pre = SizedBox(width: 30);
    Widget body = Scaffold(
      appBar: AppBar(
        title: Text('sermon app'),
      ),
      body: ListView.builder(
          itemCount: servers.length,
          itemBuilder: (context, index) {
            final ser = servers[index];
            final serverItems = <Widget>[];
            final df = DateFormat('MM-dd HH:mm:ss');
            var ss = DateTime.fromMillisecondsSinceEpoch(ser.ts * 1000);
            serverItems.add(Text('${ser.name}', style: TextStyle(color: Colors.blue)));

            serverItems.add(Text(' (${df.format(ss)})', style: TextStyle(fontSize: 14, color: Colors.grey)));

            final rootItems = <Widget>[Text('  ')];
            for (var item in ser.items) {
              final txt = Text(
                '${item.name}: ${item.v} ',
                textAlign: TextAlign.left,
                style: TextStyle(color: item.alertFlag ? Colors.red : Colors.black),
                maxLines: 1000,
              );
              rootItems.add(txt);
            }

            final appList = <Widget>[];
            for (var group in ser.groups) {
              var items = <Widget>[];
              items.add(Text('  ${group.name} -> ', textAlign: TextAlign.left));

              final lstRows = <Widget>[]; // 별도 행으로 표시할 아이템은 여기에
              print('item - ${group.items}');
              var cellCnt = 0;
              if (group.items != null) {
                for (var item in group.items) {
                  if (item.name == '__grid') {
                    cellCnt = int.parse(item.v);
                    lstRows.add(Wrap(children: items));
                    items = <Widget>[pre];
                    continue;
                  }
                  // print('name ${item.name} - ${item.v} - $cellCnt');
                  final txt = Text('${item.name}: ${item.v} ',
                      textAlign: TextAlign.left, style: TextStyle(color: item.alertFlag ? Colors.red : Colors.black));
                  if (cellCnt == 0) {
                    items.add(txt);
                  } else {
                    items.add(txt);
                    if (items.length - 1 >= cellCnt) {
                      for (var i = 1; i < items.length; ++i) {
                        items[i] = Expanded(child: items[i]);
                      }
                      lstRows.add(Row(children: items));
                      items = <Widget>[pre];
                    }
                  }
                }
              }

              // if (lstRows.length > 0) {
              if (items.isNotEmpty) {
                if (cellCnt == 0) {
                  lstRows.add(Wrap(children: items));
                } else {
                  for (var i = 1; i < items.length; ++i) {
                    items[i] = Expanded(child: items[i]);
                  }
                  final remain = cellCnt - (items.length - 1) % cellCnt;
                  for (var i = 0; i < remain; ++i) {
                    items.add(Expanded(child: SizedBox()));
                  }
                  lstRows.add(Row(children: items));
                }
              }
              appList.add(Column(
                children: lstRows,
                crossAxisAlignment: CrossAxisAlignment.start,
              ));
            }

            appList.insert(0, Row(children: serverItems));
            appList.insert(1, Row(children: rootItems));
            return ListTile(
              title: Column(
                children: appList,
                mainAxisAlignment: MainAxisAlignment.start,
                crossAxisAlignment: CrossAxisAlignment.start,
              ),
            );
            // }
          }),
      floatingActionButton: FloatingActionButton(
        onPressed: _refresh,
        tooltip: 'Check',
        child: Icon(Icons.add),
      ),
    );

    return body;
  }
}
