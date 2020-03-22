import 'dart:convert';
import 'package:flutter/material.dart';

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
class Server {
  Server();
  factory Server.fromJson(Map<String, dynamic> json) => _$ServerFromJson(json);
  Map<String, dynamic> toJson() => _$ServerToJson(this);

  String name;
}

class _ServerStatusPageState extends State<ServerStatusPage> {
  int _counter = 0;
  List<Server> servers = [];
  
  Future<void> _refresh() async {
    await doStatus();
    setState(() {});
  }

  Future<void> doStatus() async {
    var pk = {'type': 'status'};
    final ss = jsonEncode(pk);
    final res = await http.post('http://localhost:25090/cmd', body: ss).timeout(const Duration(seconds: 30));
    if(res.statusCode != 200) {
      throw Exception('http error code - ${res.statusCode} - [${res.body}]');
    }
    final map = json.decode(res.body) as List<Map<String, dynamic>>;
    List<Server> newServers = [];
    for(final item in map) {
      newServers.add(Server.fromJson(item));
    }
    servers = newServers;
    print('server - ${servers}');
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
            title: Text('${ser.name}'),
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
