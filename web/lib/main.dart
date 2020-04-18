import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';


import 'package:http/http.dart' as http;
import 'package:json_annotation/json_annotation.dart';

part 'main.g.dart';


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

@JsonSerializable()
class StItem {
  StItem(this.name, this.alertFlag, this.v);
  factory StItem.fromJson(Map<String, dynamic> json) => _$StItemFromJson(json);
  Map<String, dynamic> toJson() => _$StItemToJson(this);

  String name;
  bool alertFlag;
  String v;
}

@JsonSerializable(explicitToJson: true)
class StGroup {
  StGroup(this.name, this.items);
  factory StGroup.fromJson(Map<String, dynamic> json) => _$StGroupFromJson(json);
  Map<String, dynamic> toJson() => _$StGroupToJson(this);

  String name;
  List<StItem> items;
}

@JsonSerializable(explicitToJson: true)
class StServer {
  StServer(this.name, this.items, this.groups);
  factory StServer.fromJson(Map<String, dynamic> json) => _$StServerFromJson(json);
  Map<String, dynamic> toJson() => _$StServerToJson(this);

  String name;
  List<StItem> items;
  List<StGroup> groups;
}

String duration2str(Duration d) {
  String td(int n) {
    if (n >= 10) return "$n";
    return "0$n";
  }

  String ss = '${td(d.inMinutes.remainder(60))}:${td(d.inSeconds.remainder(60))}';
  if(d.inDays != 0 || d.inHours != 0) {
    ss = '${td(d.inHours)}:'+ss;
    if(d.inDays != 0) {
      ss = '${d.inDays}D ' + ss;
    }
  }

  return ss;
}

class _ServerStatusPageState extends State<ServerStatusPage> {
  List<StServer> servers = [];
  
  Future<void> _refresh() async {
    await doStatus();
    setState(() {});
  }

  Future<void> doStatus() async {
    var pk = {'type': 'status'};
    final ss = jsonEncode(pk);

    var url = 'http://localhost:25090/cmd';
    if(kReleaseMode) {
      url = 'https://sermon.mmx.kr/cmd';
    }

    final res = await http.post(url, body: ss).timeout(const Duration(seconds: 30));
    if(res.statusCode != 200) {
      throw Exception('http error code - ${res.statusCode} - [${res.body}]');
    }
    final map = json.decode(res.body) as List<dynamic>;
    print('map - $map');


    List<StServer> newServers = [];
    for(final item in map) {
      newServers.add(StServer.fromJson(item));
    }
    servers = newServers;
    //print('server - $servers');
  }

  void _initCode() async {
    while(true) {
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
    return Scaffold(
      appBar: AppBar(
        title: Text('sermon app'),
      ),
      body: ListView.builder(
        itemCount: servers.length,
        itemBuilder: (context, index) {
          final ser = servers[index];
          final lst = List<Widget>();
          lst.add(Text('${ser.name} - '));

          for(var item in ser.items) {
            final txt = Text('${item.name}: ${item.v} ', 
              textAlign: TextAlign.left,
              style: TextStyle(color: item.alertFlag ? Colors.red : Colors.black));
            lst.add(txt);
          }

          final lstGroup = <Widget>[];
          //for(var i = 0; i < ser.groups.length; ++i) {
          //  final group = ser.groups[i];
          for(var group in ser.groups) {
            final children = <Widget>[];
            children.add(Text('  ${group.name} -> ', textAlign: TextAlign.left));

            final lstRows = <Widget>[]; // 별도 행으로 표시할 아이템은 여기에
            print('item - ${group.items}');
            if(group.items != null) {
              for(var item in group.items) {
                final txt = Text('${item.name}: ${item.v}', textAlign: TextAlign.left,
                  style: TextStyle(color: item.alertFlag ? Colors.red : Colors.black));
                children.add(txt);
              }
            }

            if(lstRows.length > 0) {
              lstRows.insert(0, Row(children: children));
              lstGroup.add(Column(children: lstRows));
            } else {
              lstGroup.add(Row(children: children));
            }
          }

          if(lstGroup.length == 0) {
            return ListTile(
              title: Row(children: lst),
            );
          } else {
            lstGroup.insert(0, Row(children: lst));
            return ListTile(
              title: Column(children: lstGroup),
            );
          }
        }
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _refresh,
        tooltip: 'Check',
        child: Icon(Icons.add),
      ),
    );
  }
}
