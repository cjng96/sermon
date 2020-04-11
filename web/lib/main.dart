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

@JsonSerializable(explicitToJson: true)
class StDisk {
  StDisk();
  factory StDisk.fromJson(Map<String, dynamic> json) => _$StDiskFromJson(json);
  Map<String, dynamic> toJson() => _$StDiskToJson(this);

  int free;
  int total;
  int used;

  String status() {
    final totGB = total / 1024/1024/1024;
    final freeGB = free / 1024/1024/1024;
    return '${freeGB.toStringAsFixed(1)}G/${totGB.toStringAsFixed(1)}G';
  }
}

@JsonSerializable(explicitToJson: true)
class StMem {
  StMem();
  factory StMem.fromJson(Map<String, dynamic> json) => _$StMemFromJson(json);
  Map<String, dynamic> toJson() => _$StMemToJson(this);


  int total;
  double percent;

  String status() {
    final totMB = (total / 1024/1024).round();
    return '$percent%(${totMB}MB)';
  }
}

@JsonSerializable(explicitToJson: true)
class StSwap {
  StSwap();
  factory StSwap.fromJson(Map<String, dynamic> json) => _$StSwapFromJson(json);
  Map<String, dynamic> toJson() => _$StSwapToJson(this);

  int total;
  double percent;

  String status() {
    final totMB = (total / 1024/1024).round();
    return '$percent%(${totMB}MB)';
  }
}
@JsonSerializable(explicitToJson: true)
class StStatus {
  StStatus();
  factory StStatus.fromJson(Map<String, dynamic> json) => _$StStatusFromJson(json);
  Map<String, dynamic> toJson() => _$StStatusToJson(this);

  double cpu;
  StDisk disk;
  StMem mem;
  StSwap swap;
  Map<String, dynamic> apps;
}

class StItem {
  String name;
  String status;
  bool alertFlag;

  StItem(this.name, this.status, this.alertFlag);
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

@JsonSerializable(explicitToJson: true)
class Server {
  Server();
  factory Server.fromJson(Map<String, dynamic> json) => _$ServerFromJson(json);
  Map<String, dynamic> toJson() => _$ServerToJson(this);

  String name;
  StStatus status;

  List<StItem> getStatus() {
    final lst = List<StItem>();
    if(status.cpu != null) {
      lst.add(StItem('cpu', '${status.cpu}', status.cpu > 80));
    }
    if(status.mem != null) {
      lst.add(StItem('mem', '${status.mem.status()}', false));
    }
    if(status.swap != null) {
      lst.add(StItem('swap', '${status.swap.status()}', false));
    }
    if(status.disk != null) {
      lst.add(StItem('disk', '${status.disk.status()}', false));
    }

    if(status.apps != null) {
      final apps = status.apps;
      for(var app in apps.keys) {
        final ts = apps[app]['ts'];
        final now = DateTime.now().millisecondsSinceEpoch/1000;
        final d = Duration(seconds: (now-ts).round());
        lst.add(StItem(app, '${duration2str(d)}', d.inSeconds > 10));
      }
    }
    return lst;
  }

}

class _ServerStatusPageState extends State<ServerStatusPage> {
  List<Server> servers = [];
  
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
    print('map - ${map}');


    List<Server> newServers = [];
    for(final item in map) {
      newServers.add(Server.fromJson(item as Map<String, dynamic>));
    }
    print('new ser - ${newServers[0].status.mem}');
    servers = newServers;
    print('server - $servers');
  }

  void _initCode() async {
    await _refresh();
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
          final lstSt = servers[index].getStatus();
          final lst = List<Widget>();
          lst.add(Text('${servers[index].name} - '));
          for(var item in lstSt) {
            final txt = Text('${item.name}: ${item.status} ', 
              textAlign: TextAlign.left,
              style: TextStyle(color: item.alertFlag ? Colors.red : Colors.black));
            lst.add(txt);
          }

          return ListTile(
            title: Row(children: lst),
          );

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
