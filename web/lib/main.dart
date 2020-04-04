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
    final usedGB = used / 1024/1024/1024;
    return '${usedGB.toStringAsFixed(1)}/${totGB.toStringAsFixed(1)}';
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
    final usedMB = (used / 1024/1024).round();
    return '$usedMB/$totMB';
  }
}

@JsonSerializable(explicitToJson: true)
class StSystem {
  StSystem();
  factory StSystem.fromJson(Map<String, dynamic> json) => _$StSystemFromJson(json);
  Map<String, dynamic> toJson() => _$StSystemToJson(this);

  double cpu;
  StDisk disk;
  StMem mem;
}

@JsonSerializable(explicitToJson: true)
class Server {
  Server();
  factory Server.fromJson(Map<String, dynamic> json) => _$ServerFromJson(json);
  Map<String, dynamic> toJson() => _$ServerToJson(this);

  String name;
  StSystem system;
}

class _ServerStatusPageState extends State<ServerStatusPage> {
  List<Server> servers = [];
  
  Future<void> _refresh() async {
    await doStatus();
    setState(() {});
  }

  Future<void> doStatus() async {
    print('doStatus');
    var pk = {'type': 'status'};
    final ss = jsonEncode(pk);

    var url = 'http://localhost:25090/cmd';
    if(kReleaseMode) {
      url = 'https://sermon.mmx.kr/cmd';
    }

    print('doStatus2');
    final res = await http.post(url, body: ss).timeout(const Duration(seconds: 30));
    if(res.statusCode != 200) {
      throw Exception('http error code - ${res.statusCode} - [${res.body}]');
    }
    print('doStatus3 - ${res.body}');
    final map = json.decode(res.body) as List<dynamic>;
    List<Server> newServers = [];
    for(final item in map) {
      newServers.add(Server.fromJson(item as Map<String, dynamic>));
    }
    print('doStatus4');
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
          return ListTile(
            title: Text('${ser.name} - cpu: ${ser.system.cpu}, mem:${ser.system.mem.status()}, disk:${ser.system.disk.status()}'),
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
