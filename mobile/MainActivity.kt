package com.candyland.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import com.candyland.app.navigation.CandylandApp
import com.candyland.app.ui.theme.CandylandTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            CandylandTheme {
                CandylandApp()
            }
        }
    }
}
