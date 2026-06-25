package id.sapisehat.sapisehat_mobile

import android.content.Intent
import androidx.core.content.FileProvider
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import java.io.File

class MainActivity : FlutterActivity() {
    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "id.sapisehat/share").setMethodCallHandler { call, result ->
            if (call.method != "shareFile") {
                result.notImplemented()
                return@setMethodCallHandler
            }
            val path = call.argument<String>("path")
            val mimeType = call.argument<String>("mimeType") ?: "application/pdf"
            val text = call.argument<String>("text") ?: ""
            if (path.isNullOrBlank()) {
                result.error("missing_path", "Missing file path", null)
                return@setMethodCallHandler
            }
            val file = File(path)
            if (!file.exists()) {
                result.error("missing_file", "File does not exist", null)
                return@setMethodCallHandler
            }
            val sharedDir = File(cacheDir, "shared").apply { mkdirs() }
            val shareFile = File(sharedDir, file.name)
            file.copyTo(shareFile, overwrite = true)
            val uri = FileProvider.getUriForFile(this, "${applicationContext.packageName}.fileprovider", shareFile)
            val intent = Intent(Intent.ACTION_SEND).apply {
                type = mimeType
                putExtra(Intent.EXTRA_STREAM, uri)
                putExtra(Intent.EXTRA_TEXT, text)
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            }
            startActivity(Intent.createChooser(intent, text.ifBlank { "Bagikan laporan" }))
            result.success(null)
        }
    }
}
