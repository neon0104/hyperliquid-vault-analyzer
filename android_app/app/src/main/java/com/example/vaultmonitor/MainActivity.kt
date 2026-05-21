package com.example.vaultmonitor

import android.annotation.SuppressLint
import android.content.Context
import android.os.Bundle
import android.view.ViewGroup
import android.webkit.CookieManager
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import com.example.vaultmonitor.theme.VaultMonitorTheme

class MainActivity : ComponentActivity() {

    private val PREFS_NAME = "VaultPrefs"
    private val KEY_URL = "DashboardUrl"
    private val DEFAULT_URL = "http://10.0.2.2:5001" 

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        setContent {
            VaultMonitorTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    var currentUrl by remember { mutableStateOf(getStoredUrl()) }
                    var showDialog by remember { mutableStateOf(false) }

                    // 도메인 입력 다이얼로그
                    if (showDialog) {
                        var tempUrl by remember { mutableStateOf(currentUrl) }
                        AlertDialog(
                            onDismissRequest = { showDialog = false },
                            title = { Text("대시보드 주소 설정") },
                            text = {
                                OutlinedTextField(
                                    value = tempUrl,
                                    onValueChange = { tempUrl = it },
                                    label = { Text("프라이빗 URL (예: https://...)") },
                                    singleLine = true,
                                    modifier = Modifier.fillMaxWidth()
                                )
                            },
                            confirmButton = {
                                Button(
                                    onClick = {
                                        saveUrl(tempUrl)
                                        currentUrl = tempUrl
                                        showDialog = false
                                        Toast.makeText(this@MainActivity, "설정이 저장되었습니다.", Toast.LENGTH_SHORT).show()
                                    }
                                ) {
                                    Text("저장")
                                }
                            },
                            dismissButton = {
                                TextButton(onClick = { showDialog = false }) {
                                    Text("취소")
                                }
                            }
                        )
                    }

                    Box(modifier = Modifier.fillMaxSize()) {
                        WebViewContainer(url = currentUrl)
                        
                        // 우측 상단 플로팅 설정 버튼 (⚙️ 이모지 텍스트를 사용하여 빌드 라이브러리 충돌 우회)
                        FloatingActionButton(
                            onClick = { showDialog = true },
                            modifier = Modifier
                                .align(Alignment.TopEnd)
                                .padding(16.dp)
                                .size(48.dp),
                            containerColor = MaterialTheme.colorScheme.primaryContainer
                        ) {
                            Text("⚙️", style = MaterialTheme.typography.titleMedium)
                        }
                    }
                }
            }
        }
    }

    private fun getStoredUrl(): String {
        val prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        return prefs.getString(KEY_URL, DEFAULT_URL) ?: DEFAULT_URL
    }

    private fun saveUrl(url: String) {
        val prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().putString(KEY_URL, url).apply()
    }
}

@SuppressLint("SetJavaScriptEnabled")
@Composable
fun WebViewContainer(url: String) {
    AndroidView(
        factory = { context ->
            WebView(context).apply {
                layoutParams = ViewGroup.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.MATCH_PARENT
                )
                webViewClient = object : WebViewClient() {
                    override fun shouldOverrideUrlLoading(view: WebView?, url: String?): Boolean {
                        url?.let { view?.loadUrl(it) }
                        return true
                    }
                }
                
                // 쿠키 설정 보존
                val cookieManager = CookieManager.getInstance()
                cookieManager.setAcceptCookie(true)
                cookieManager.setAcceptThirdPartyCookies(this, true)
                
                settings.apply {
                    javaScriptEnabled = true
                    domStorageEnabled = true
                    databaseEnabled = true
                    useWideViewPort = true
                    loadWithOverviewMode = true
                    mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
                }
                
                loadUrl(url)
            }
        },
        update = { webView ->
            // URL이 달라진 경우에만 로딩하여 무한 루프 로딩 방지
            if (webView.url != url) {
                webView.loadUrl(url)
            }
        },
        modifier = Modifier.fillMaxSize()
    )
}
