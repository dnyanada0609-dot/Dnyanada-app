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
import java.util.Locale;

public class MainActivity extends BridgeActivity {
    private WebView printWebView;
    private long backPressedTime = 0L;
    private boolean printPreviewLaunched = false;
    private boolean leftForPrintPreview = false;
    private boolean justReturnedFromPrint = false;

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getBridge().getWebView().addJavascriptInterface(new Object() {
            @JavascriptInterface
            public void printHtml(final String html, final String title) {
                runOnUiThread(() -> openPrintPreview(html, title));
            }
        }, "AndroidPrint");

        getOnBackPressedDispatcher().addCallback(this, new OnBackPressedCallback(true) {
            @Override public void handleOnBackPressed() {
                WebView main = getBridge() == null ? null : getBridge().getWebView();
                if (justReturnedFromPrint) {
                    justReturnedFromPrint = false;
                    backPressedTime = 0L;
                    // The Android print UI has already closed. Keep the current app screen.
                    return;
                }
                if (main != null && main.canGoBack()) {
                    backPressedTime = 0L;
                    main.goBack();
                } else if (System.currentTimeMillis() - backPressedTime < 2000L) {
                    finish();
                } else {
                    backPressedTime = System.currentTimeMillis();
                    Toast.makeText(MainActivity.this, "Press back again to exit", Toast.LENGTH_SHORT).show();
                }
            }
        });
    }

    private void openPrintPreview(String html, String title) {
        if (html == null || html.trim().isEmpty()) {
            Toast.makeText(this, "Print HTML is empty", Toast.LENGTH_LONG).show();
            return;
        }
        FrameLayout root = findViewById(android.R.id.content);
        if (root == null) return;
        // Do not destroy the WebView of a previous print job while Android still uses it.
        // Retain the most recent print WebView until a subsequent print request.
        if (printWebView != null) {
            try {
                root.removeView(printWebView);
                printWebView.destroy();
            } catch (Exception ignored) { }
            printWebView = null;
        }
        WebView view = new WebView(this);
        view.setAlpha(1.0f);
        view.getSettings().setJavaScriptEnabled(true);
        view.getSettings().setDefaultTextEncodingName("UTF-8");
        // Attach the print WebView BEHIND the main app, not on top of its controls.
        root.addView(view, 0, new FrameLayout.LayoutParams(1080, 1600));
        printWebView = view;
        printPreviewLaunched = false;
        leftForPrintPreview = false;
        justReturnedFromPrint = false;
        backPressedTime = 0L;

        view.setWebViewClient(new WebViewClient() {
            private boolean queued = false;
            @Override public void onPageFinished(WebView finishedView, String url) {
                if (queued) return;
                queued = true;
                finishedView.postDelayed(() -> {
                    if (isFinishing() || printWebView != finishedView) return;
                    PrintManager manager = (PrintManager) getSystemService(Context.PRINT_SERVICE);
                    if (manager == null) return;
                    String job = title == null || title.trim().isEmpty() ? "Dnyanada_Report" : title;
                    PrintDocumentAdapter adapter = finishedView.createPrintDocumentAdapter(job);
                    String lower = html.toLowerCase(Locale.ROOT);
                    boolean legal = lower.matches("(?s).*@page\\s*\\{[^}]*size\\s*:\\s*legal.*") || lower.contains("size:legal");
                    boolean landscape = lower.matches("(?s).*@page\\s*\\{[^}]*size\\s*:\\s*[^;}]*landscape.*");
                    PrintAttributes.MediaSize size = legal ? PrintAttributes.MediaSize.NA_LEGAL : PrintAttributes.MediaSize.ISO_A4;
                    if (landscape) size = size.asLandscape();
                    PrintAttributes attributes = new PrintAttributes.Builder()
                            .setMediaSize(size)
                            .setMinMargins(PrintAttributes.Margins.NO_MARGINS)
                            .setColorMode(PrintAttributes.COLOR_MODE_COLOR)
                            .build();
                    try {
                        printPreviewLaunched = true;
                        manager.print(job, adapter, attributes);
                    } catch (Exception ex) {
                        printPreviewLaunched = false;
                        Toast.makeText(MainActivity.this, "Unable to open print preview", Toast.LENGTH_LONG).show();
                    }
                }, 1200L);
            }
        });
        view.loadDataWithBaseURL("file:///android_asset/public/", html, "text/html", "UTF-8", null);
    }

    @Override public void onPause() {
        if (printPreviewLaunched) leftForPrintPreview = true;
        super.onPause();
    }

    @Override public void onResume() {
        super.onResume();
        if (leftForPrintPreview) {
            leftForPrintPreview = false;
            printPreviewLaunched = false;
            justReturnedFromPrint = true;
            backPressedTime = 0L;
        }
    }

    @Override public void onDestroy() {
        if (printWebView != null) {
            try {
                FrameLayout root = findViewById(android.R.id.content);
                if (root != null) root.removeView(printWebView);
                printWebView.destroy();
            } catch (Exception ignored) { }
            printWebView = null;
        }
        super.onDestroy();
    }
}
