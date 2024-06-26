import 'dart:convert';
import 'dart:ui';

import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';

import 'package:http/http.dart' as http;
import 'package:intl/intl.dart';
import 'package:json_annotation/json_annotation.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:percent_indicator/percent_indicator.dart';

import 'platformOther.dart' if (kIsWeb) 'platformWeb.dart';

enum WarningStatus {
  ERROR('e', 'E'), // 바로 초치해야하는 수준
  WARNING('w', 'W'), // 당장 문제는 없지만 예의주시
  NORMAL('n', 'N'); // 정상

  final String lowerCaseValue;
  final String upperCaseValue;

  const WarningStatus(this.lowerCaseValue, this.upperCaseValue);
}

void main() => runApp(MyApp());

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Sermon',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        // textTheme: GoogleFonts.robotoMonoTextTheme(),
        // textTheme: GoogleFonts.abelTextTheme(),
      ),
      home: ServerStatusPage(),
    );
  }
}

class ServerStatusPage extends StatefulWidget {
  ServerStatusPage({Key? key}) : super(key: key);

  @override
  _ServerStatusPageState createState() => _ServerStatusPageState();
}

class StItem {
  StItem(this.name, this.alertFlag, this.type, this.v);
  factory StItem.fromJson(Map<String, dynamic> json) => StItem(
        json['name'] as String,
        json['alertFlag'] as String? ?? WarningStatus.NORMAL.lowerCaseValue,
        json['type'] as String? ?? '',
        json['v'] as String? ?? '', // name:newline, type:sp의 경우 v가 없다
      );
  Map<String, dynamic> toJson() => <String, dynamic>{
        'name': name,
        'type': type,
        'alertFlag': alertFlag,
        'v': v,
      };

  String name;
  String type; // ''(일반적), 'sp'(newline등)
  String alertFlag;
  String v;
}

class StGroup {
  StGroup(this.name, this.items);
  factory StGroup.fromJson(Map<String, dynamic> json) {
    final items = json['items'] as List;

    return StGroup(
      json['name'] as String,
      items.map((e) => StItem.fromJson(e as Map<String, dynamic>)).toList(),
    );
  }
  Map<String, dynamic> toJson() => <String, dynamic>{
        'name': name,
        'items': items.map((e) => e.toJson()).toList(),
      };

  String name;
  List<StItem> items;
}

class StServer {
  StServer(this.name, this.ts, this.items, this.groups);
  factory StServer.fromJson(Map<String, dynamic> json) {
    final items = json['items'] as List;
    final groups = json['groups'] as List;

    if (!json.containsKey('ts')) {
      print('ts not found - $json');
    }

    return StServer(
      json['name'] as String,
      json['ts'] as int? ?? 0,
      items.map((e) => StItem.fromJson(e as Map<String, dynamic>)).toList(),
      groups.map((e) => StGroup.fromJson(e as Map<String, dynamic>)).toList(),
    );
  }

  Map<String, dynamic> toJson() => <String, dynamic>{
        'name': name,
        'ts': ts,
        'items': items.map((e) => e.toJson()).toList(),
        'groups': groups.map((e) => e.toJson()).toList()
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

// alertLevel별 알맞는 색상 추출
Color getErrCr(String alertFlag, Color defaultColor) {
  if (alertFlag == WarningStatus.ERROR.lowerCaseValue || alertFlag == WarningStatus.ERROR.upperCaseValue) {
    return Colors.red;
  } else if (alertFlag == WarningStatus.WARNING.lowerCaseValue || alertFlag == WarningStatus.WARNING.upperCaseValue) {
    return Colors.orange;
  } else {
    return defaultColor;
  }
}

class _ServerStatusPageState extends State<ServerStatusPage> {
  String name = 'sermon';
  bool fixedFont = false;
  List<StServer> servers = [];

  Future<void> _refresh() async {
    try {
      await doStatus();
    } catch (e) {
      print(e);
    }
    setState(() {});
  }

  Future doStatus() async {
    var pk = {'type': 'status'};
    final ss = jsonEncode(pk);

    // var url = 'http://localhost:25090/cmd';
    // if (kReleaseMode) {

    const urlEnv = kReleaseMode
        ? String.fromEnvironment('SERVER_URL', defaultValue: 'http://localhost:25090/cmd')
        : 'http://sermon.retailtrend.net/cmd';
    var url = urlEnv;
    //url = 'https://sermon.mmx.kr:33/cmd';

    print('url - $url');
    final res = await http.post(Uri.parse(url), body: ss).timeout(const Duration(seconds: 30));
    if (res.statusCode != 200) {
      throw Exception('http error code - ${res.statusCode} - [${res.body}]');
    }
    final map = json.decode(res.body) as Map;
    print('map - $map');

    name = map['name'] as String? ?? name;
    fixedFont = map['fixedFont'] as bool? ?? false;

    List<StServer> newServers = [];
    final serverList = map['servers'] as List;
    for (final item in serverList) {
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
    var safeName = name;
    setTitle(safeName);

    Widget pre = SizedBox(width: 30);
    Widget body = ListView.builder(
        itemCount: servers.length,
        itemBuilder: (context, index) {
          final ser = servers[index];

          final df = DateFormat('MMdd HH:mm:ss');
          var ss = DateTime.fromMillisecondsSinceEpoch(ser.ts * 1000);
          // 제일 첫줄에 출력할 서버명과 시간
          final serverItems = <Widget>[];
          serverItems.add(Text('${ser.name}',
              style: TextStyle(
                color: Colors.black54,
                fontFeatures: [FontFeature.tabularFigures()],
              )));
          serverItems.add(Text(' (${df.format(ss)})',
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey,
                fontFeatures: [FontFeature.tabularFigures()],
              )));

          final rows = <Widget>[];
          Widget serverRow = Row(children: serverItems);
          serverRow = ColoredBox(child: serverRow, color: Colors.blue.withAlpha(40));

          rows.insert(0, serverRow);

          // 서버 자체 속성들 - rootRows로 rows앞쪽에 추가된다
          var rootItems = <Widget>[Text('  ')];
          for (final item in ser.items) {
            if (item.type == 'sp') {
              switch (item.name) {
                case 'newline':
                  rootItems = <Widget>[Text('  ')];
                  rows.add(Row(children: rootItems));
                  break;
              }
            } else {
              Widget? w;
              print('item name - ${item.name} - ${item.v}');
              final sizeRE = RegExp(r'(\d+)G/(\d+)G');
              switch (item.name) {
                case 'mem':
                case 'swap':
                  // 54%(62792MB)
                  final percentRE = RegExp(r'(\d+)%\((\d+.+)\)');
                  final m = percentRE.firstMatch(item.v);
                  if (m != null) {
                    final percent = int.parse(m.group(1)!);
                    final total = m.group(2);

                    Color cr = getErrCr(item.alertFlag, Colors.blue.withAlpha(40));
                    w = LinearPercentIndicator(
                      width: 150.0,
                      animation: true,
                      animationDuration: 100,
                      lineHeight: 20.0,
                      leading: Text("${item.name}:"),
                      // trailing: const Text("right"),
                      percent: percent / 100,
                      center: Text("$percent%($total)"),
                      progressColor: cr,
                      barRadius: Radius.circular(7),
                    );
                    // w = SizedBox(child: w, width: 200);
                    // w = Row(children: [Text('${item.name}:'), w]);
                    w = IntrinsicWidth(child: w);
                  }
                  break;
                case 'disk':
                default: // mongo, ftp...
                  // 23G/29G
                  final m = sizeRE.firstMatch(item.v);
                  if (m != null) {
                    final used = int.parse(m.group(1)!);
                    final total = int.parse(m.group(2)!);
                    Color cr = getErrCr(item.alertFlag, Colors.blue.withAlpha(40));
                    w = LinearPercentIndicator(
                      width: 150.0,
                      animation: true,
                      animationDuration: 100,
                      lineHeight: 20.0,
                      leading: Text("${item.name}:"),
                      // trailing: const Text("right"),
                      percent: used / total,
                      center: Text("${used}G/${total}G"),
                      progressColor: cr,
                      barRadius: Radius.circular(7),
                    );
                    // w = ColoredBox(child: w, color: Colors.green);
                    w = IntrinsicWidth(child: w);
                  }
                  break;
              }

              if (w == null) {
                Color cr = getErrCr(item.alertFlag, Colors.black);

                w = Text(
                  '${item.name}: ${item.v} ',
                  textAlign: TextAlign.left,
                  style: TextStyle(
                    color: cr,
                    // fontFeatures: [FontFeature.tabularFigures()],
                    // fontFeatures: [FontFeature.enable('lnum')],
                  ),
                  maxLines: 1000,
                );
              }
              rootItems.add(w);
            }
          }
          // rows.add(Flex(children: rootItems, direction: Axis.horizontal));

          rows.add(Wrap(children: rootItems));

          // 여기부터 하위
          for (final group in ser.groups) {
            var items = <Widget>[];
            items.add(Text(
              '  ${group.name} -> ',
              textAlign: TextAlign.left,
              // style: TextStyle(fontFeatures: [FontFeature.tabularFigures()]),
            ));

            final lstRows = <Widget>[]; // 별도 행으로 표시할 아이템은 여기에
            print('item - ${group.items}');
            var cellCnt = 0;
            // if (group.items != null) {
            for (final item in group.items) {
              if (item.name == '__grid') {
                cellCnt = int.parse(item.v);
                lstRows.add(Wrap(children: items));
                items = <Widget>[pre];
                continue;
              }

              // print('name ${item.name} - ${item.v} - $cellCnt');
              Color cr = getErrCr(item.alertFlag, Colors.black);

              final txt = Text('${item.name}: ${item.v} ',
                  textAlign: TextAlign.left,
                  style: TextStyle(
                    color: cr,
                    // fontFeatures: [FontFeature.tabularFigures()],
                    // fontFeatures: [FontFeature.enable('lnum')],
                  ));
              if (cellCnt == 0) {
                items.add(txt);
              } else {
                items.add(txt);
                if (items.length - 1 >= cellCnt) {
                  for (var i = 1; i < items.length; ++i) {
                    items[i] = Expanded(child: items[i]);
                    // items[i] = items[i];
                  }
                  lstRows.add(Row(children: items));
                  // lstRows.add(Wrap(children: items));
                  items = <Widget>[pre];
                }
              }
            }
            // }

            // if (lstRows.length > 0) {
            if (items.isNotEmpty) {
              if (cellCnt == 0) {
                lstRows.add(Row(children: items));
              } else {
                for (var i = 1; i < items.length; ++i) {
                  items[i] = Expanded(child: items[i]);
                }
                final remain = cellCnt - (items.length - 1) % cellCnt;
                for (var i = 0; i < remain; ++i) {
                  items.add(Expanded(child: SizedBox()));
                }
                lstRows.add(Row(children: items));
                // lstRows.add(Wrap(children: items));
              }
            }
            rows.add(Column(
              children: lstRows,
              crossAxisAlignment: CrossAxisAlignment.stretch,
            ));
          }

          return ListTile(
            title: Column(
              children: rows,
              mainAxisAlignment: MainAxisAlignment.start,
              crossAxisAlignment: CrossAxisAlignment.start,
            ),
          );
          // }
        });

    if (fixedFont) {
      body = Theme(child: body, data: ThemeData(textTheme: GoogleFonts.robotoMonoTextTheme()));
    }

    body = Scaffold(
      appBar: AppBar(
        title: Text(safeName),
      ),
      body: body,
      // floatingActionButton: FloatingActionButton(
      //   onPressed: _refresh,
      //   tooltip: 'Check',
      //   child: Icon(Icons.add),
      // ),
    );

    return body;
  }
}
