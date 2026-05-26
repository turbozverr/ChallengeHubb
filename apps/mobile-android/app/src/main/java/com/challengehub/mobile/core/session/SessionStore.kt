package com.challengehub.mobile.core.session

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.sessionDataStore by preferencesDataStore("challengehub_session")

class SessionStore(private val context: Context) {
    private val tokenKey = stringPreferencesKey("mobile_token")

    val token: Flow<String?> = context.sessionDataStore.data.map { preferences ->
        preferences[tokenKey]
    }

    suspend fun saveToken(token: String) {
        context.sessionDataStore.edit { preferences ->
            preferences[tokenKey] = token
        }
    }

    suspend fun clear() {
        context.sessionDataStore.edit { preferences ->
            preferences.remove(tokenKey)
        }
    }
}
