package com.dnyanada.app;

import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.widget.Toast;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    private static final String TEACHER_URL = "https://dnyanada-app-1df67.web.app/";

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Intent browser = new Intent(Intent.ACTION_VIEW, Uri.parse(TEACHER_URL));
        browser.addCategory(Intent.CATEGORY_BROWSABLE);
        try {
            startActivity(browser);
        } catch (ActivityNotFoundException e) {
            Toast.makeText(this, "वेबसाईट उघडण्यासाठी ब्राउझर उपलब्ध नाही", Toast.LENGTH_LONG).show();
        }
        finish();
    }
}
