import 'dart:convert';
import 'dart:io';

class ApiRequest {
  ApiRequest(
    this.method,
    this.path, {
    this.body,
    this.headers = const {},
    this.formFields = const {},
    this.fileField,
    this.fileName,
    this.fileBytes,
    this.fileContentType = 'image/jpeg',
  });
  final String method;
  final String path;
  final String? body;
  final Map<String, String> headers;
  final Map<String, String> formFields;
  final String? fileField;
  final String? fileName;
  final List<int>? fileBytes;
  final String fileContentType;

  bool get isMultipart => fileField != null && fileBytes != null;
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
    if (request.isMultipart) {
      final boundary = '----sapisehat-${DateTime.now().microsecondsSinceEpoch}';
      httpRequest.headers.contentType = ContentType(
        'multipart',
        'form-data',
        parameters: {'boundary': boundary},
      );
      void writeAscii(String value) => httpRequest.add(utf8.encode(value));
      for (final entry in request.formFields.entries) {
        writeAscii('--$boundary\r\n');
        writeAscii(
          'Content-Disposition: form-data; name="${entry.key}"\r\n\r\n',
        );
        writeAscii('${entry.value}\r\n');
      }
      writeAscii('--$boundary\r\n');
      writeAscii(
        'Content-Disposition: form-data; name="${request.fileField}"; filename="${request.fileName ?? 'scan.jpg'}"\r\n',
      );
      writeAscii('Content-Type: ${request.fileContentType}\r\n\r\n');
      httpRequest.add(request.fileBytes!);
      writeAscii('\r\n--$boundary--\r\n');
    } else if (request.body != null) {
      httpRequest.headers.contentType = ContentType.json;
      httpRequest.write(request.body);
    }
    final response = await httpRequest.close();
    final body = await response.transform(utf8.decoder).join();
    client.close();
    return ApiResponse(response.statusCode, body);
  }
}
