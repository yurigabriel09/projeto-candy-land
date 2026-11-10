package com.example.candyland

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import com.example.candyland.navigation.CandylandApp
import com.example.candyland.ui.theme.CandylandTheme

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
