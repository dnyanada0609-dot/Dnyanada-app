package com.dnyanada.app;
import android.content.Context;
import android.os.Bundle;
import android.print.PrintAttributes;
import android.print.PrintDocumentAdapter;
import android.print.PrintManager;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;
import android.widget.Toast;
import androidx.activity.OnBackPressedCallback;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    private WebView printWebView;
    private long backPressedTime = 0;
    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getBridge().getWebView().addJavascriptInterface(new Object() {
            @JavascriptInterface
            public void printHtml(final String html, final String title) {
                runOnUiThread(() -> {
                    if (html == null || html.trim().isEmpty()) {
                        Toast.makeText(MainActivity.this,"Print HTML is empty",Toast.LENGTH_LONG).show();
                        return;
                    }
                    // A detached WebView often prints a blank page on Android.
                    FrameLayout root = findViewById(android.R.id.content);
                    if (printWebView != null) {
                        try { root.removeView(printWebView); printWebView.destroy(); } catch (Exception ignored) {}
                    }
                    WebView webView = new WebView(MainActivity.this);
                    webView.setAlpha(1.0f);
                    root.addView(webView, new FrameLayout.LayoutParams(1080, 1600));
                    printWebView = webView;
                    webView.getSettings().setJavaScriptEnabled(true);
                    webView.getSettings().setDefaultTextEncodingName("UTF-8");
                    webView.setWebViewClient(new WebViewClient() {
                        @Override public void onPageFinished(WebView view, String url) {
                            // Wait for web fonts and images before creating the print adapter.
                            view.postDelayed(() -> {
                                    if (printWebView != view || isFinishing()) return;
                                    PrintManager pm = (PrintManager)getSystemService(Context.PRINT_SERVICE);
                                    String job = (title != null && !title.isEmpty()) ? title : "Dnyanada_Report";
                                    PrintDocumentAdapter adapter = view.createPrintDocumentAdapter(job);
                                    String lowerHtml = html.toLowerCase(java.util.Locale.ROOT);
                                    boolean legal = lowerHtml.matches("(?s).*@page\\s*\\{[^}]*size\\s*:\\s*legal.*") || lowerHtml.contains("size:legal");
                                    boolean landscape = lowerHtml.matches("(?s).*@page\\s*\\{[^}]*size\\s*:\\s*[^;}]*landscape.*") || lowerHtml.contains("size:legal landscape");
                                    PrintAttributes.MediaSize size = legal ? PrintAttributes.MediaSize.NA_LEGAL : PrintAttributes.MediaSize.ISO_A4;
                                    if (landscape) size = size.asLandscape();
                                    PrintAttributes attrs = new PrintAttributes.Builder()
                                        .setMediaSize(size)
                                        .setMinMargins(PrintAttributes.Margins.NO_MARGINS)
                                        .setColorMode(PrintAttributes.COLOR_MODE_COLOR)
                                        .build();
                                    pm.print(job,adapter,attrs);
                                    // Keep WebView referenced while Android print preview is active.
                            },1200);
                        }
                    });
                    webView.loadDataWithBaseURL("file:///android_asset/public/",html,"text/html","UTF-8",null);
                });
            }
        }, "AndroidPrint");
        getOnBackPressedDispatcher().addCallback(this,new OnBackPressedCallback(true){
            @Override public void handleOnBackPressed(){
                WebView wv=getBridge().getWebView();
                if(wv!=null && wv.canGoBack()){wv.goBack();}
                else if(System.currentTimeMillis()-backPressedTime<2000){finish();}
                else{backPressedTime=System.currentTimeMillis();Toast.makeText(MainActivity.this,"Press back again to exit",Toast.LENGTH_SHORT).show();}
            }
        });
    }
}
