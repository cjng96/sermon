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
    return '${freeGB.toStringAsFixed(1)}/${totGB.toStringAsFixed(1)}';
  }

}

@JsonSerializable(explicitToJson: true)
class StMem {
  StMem();
  factory StMem.fromJson(Map<String, dynamic> json) => _$StMemFromJson(json);
  Map<String, dynamic> toJson() => _$StMemToJson(this);

  int free;
  int total;
  int used;
  double percent;

  String status() {
    final totMB = (total / 1024/1024).round();
    final freeMB = (free / 1024/1024).round();
    return '$freeMB/$totMB';
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
  Map<String, dynamic> apps;
}

@JsonSerializable(explicitToJson: true)
class Server {
  Server();
  factory Server.fromJson(Map<String, dynamic> json) => _$ServerFromJson(json);
  Map<String, dynamic> toJson() => _$ServerToJson(this);

  String name;
  StStatus status;
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
    List<Server> newServers = [];
    for(final item in map) {
      newServers.add(Server.fromJson(item as Map<String, dynamic>));
    }
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
          final ser = servers[index];
          var ss = '';
          if(ser.status.cpu == null) {
            ss = '${ser.name} - ';
            final apps = ser.status.apps;
            for(var app in apps.keys) {
              ss += '$app: ${apps[app]['ts']} ';
            }
          } else {
            ss = '${ser.name} - cpu: ${ser.status.cpu}, mem: ${ser.status.mem.status()}, disk: ${ser.status.disk.status()}';
          }

          return ListTile(
            title: Text(ss),
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
