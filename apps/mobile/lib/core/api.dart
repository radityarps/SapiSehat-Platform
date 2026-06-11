import 'dart:convert';
import 'dart:io';

class ApiRequest {
  ApiRequest(this.method, this.path, {this.body, this.headers = const {}});
  final String method;
  final String path;
  final String? body;
  final Map<String, String> headers;
}

class ApiResponse {
  ApiResponse(this.statusCode, this.body);
  final int statusCode;
  final String body;
  Map<String, dynamic> get json => jsonDecode(body) as Map<String, dynamic>;
}

abstract class ApiTransport {
  Future<ApiResponse> send(ApiRequest request);
}

class ApiConfig {
  static const defaultBaseUrl = 'http://10.0.2.2:8000';
  static String baseUrl = defaultBaseUrl;
}

class HttpApiTransport implements ApiTransport {
  HttpApiTransport({String? baseUrl}) : baseUrl = baseUrl ?? ApiConfig.baseUrl;
  final String baseUrl;

  @override
  Future<ApiResponse> send(ApiRequest request) async {
    final uri = Uri.parse('$baseUrl${request.path}');
    final client = HttpClient();
    final httpRequest = await client.openUrl(request.method, uri);
    request.headers.forEach(httpRequest.headers.set);
    if (request.body != null) {
      httpRequest.headers.contentType = ContentType.json;
      httpRequest.write(request.body);
    }
    final response = await httpRequest.close();
    final body = await response.transform(utf8.decoder).join();
    client.close();
    return ApiResponse(response.statusCode, body);
  }
}
