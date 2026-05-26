package com.challengehub.mobile.feature.auth

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.challengehub.mobile.core.design.Background
import com.challengehub.mobile.core.design.TextMuted
import com.challengehub.mobile.core.network.LoginRequestDto
import com.challengehub.mobile.core.network.NetworkModule
import com.challengehub.mobile.core.network.RegisterRequestDto
import kotlinx.coroutines.launch

@Composable
fun AuthScreen(onAuthenticated: (String) -> Unit) {
    val scope = rememberCoroutineScope()
    var isRegister by remember { mutableStateOf(false) }
    var username by remember { mutableStateOf("demo_user") }
    var fullName by remember { mutableStateOf("Demo User") }
    var email by remember { mutableStateOf("user@challengehub.local") }
    var password by remember { mutableStateOf("user123") }
    var error by remember { mutableStateOf<String?>(null) }
    var loading by remember { mutableStateOf(false) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Background)
            .padding(24.dp),
        verticalArrangement = Arrangement.Center,
    ) {
        Text("ChallengeHub", fontSize = 36.sp)
        Text("Короткі відео. Челенджі. XP.", color = TextMuted)
        Spacer(Modifier.height(32.dp))
        if (isRegister) {
            OutlinedTextField(value = username, onValueChange = { username = it }, label = { Text("Нікнейм") }, modifier = Modifier.fillMaxWidth())
            Spacer(Modifier.height(10.dp))
            OutlinedTextField(value = fullName, onValueChange = { fullName = it }, label = { Text("Ім'я") }, modifier = Modifier.fillMaxWidth())
            Spacer(Modifier.height(10.dp))
        }
        OutlinedTextField(value = email, onValueChange = { email = it }, label = { Text("Email") }, modifier = Modifier.fillMaxWidth())
        Spacer(Modifier.height(10.dp))
        OutlinedTextField(
            value = password,
            onValueChange = { password = it },
            label = { Text("Пароль") },
            visualTransformation = PasswordVisualTransformation(),
            modifier = Modifier.fillMaxWidth(),
        )
        if (error != null) {
            Spacer(Modifier.height(12.dp))
            Text(error.orEmpty(), color = androidx.compose.ui.graphics.Color(0xFFFF6B6B))
        }
        Spacer(Modifier.height(20.dp))
        Button(
            enabled = !loading,
            onClick = {
                loading = true
                error = null
                scope.launch {
                    runCatching {
                        if (isRegister) {
                            NetworkModule.api.register(RegisterRequestDto(username, fullName, email, password))
                        } else {
                            NetworkModule.api.login(LoginRequestDto(email, password))
                        }
                    }.onSuccess {
                        onAuthenticated(it.accessToken)
                    }.onFailure {
                        error = "Не вдалося увійти. Перевірте дані або backend URL."
                    }
                    loading = false
                }
            },
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text(if (isRegister) "Зареєструватися" else "Увійти")
        }
        TextButton(onClick = { isRegister = !isRegister }) {
            Text(if (isRegister) "У мене вже є акаунт" else "Створити акаунт")
        }
    }
}
