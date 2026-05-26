package com.challengehub.mobile.core.network

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class MobileUserDto(
    val id: String,
    val username: String,
    @SerialName("full_name") val fullName: String,
    val email: String,
    @SerialName("avatar_url") val avatarUrl: String? = null,
    val bio: String? = null,
    val xp: Int,
    @SerialName("is_premium") val isPremium: Boolean,
    val status: String,
    @SerialName("created_at") val createdAt: String,
)

@Serializable
data class TokenDto(
    @SerialName("access_token") val accessToken: String,
    @SerialName("token_type") val tokenType: String,
    val user: MobileUserDto,
)

@Serializable
data class LoginRequestDto(val email: String, val password: String)

@Serializable
data class RegisterRequestDto(
    val username: String,
    @SerialName("full_name") val fullName: String,
    val email: String,
    val password: String,
)

@Serializable
data class ChallengeDto(
    val id: String,
    val title: String,
    val description: String,
    val difficulty: String,
    @SerialName("duration_days") val durationDays: Int,
    @SerialName("xp_reward") val xpReward: Int,
    @SerialName("challenge_type") val challengeType: String,
    val status: String,
    @SerialName("created_at") val createdAt: String,
    @SerialName("creator_name") val creatorName: String? = null,
)

@Serializable
data class VideoDto(
    val id: String,
    @SerialName("challenge_id") val challengeId: String,
    @SerialName("challenge_type") val challengeType: String = "SPONSORED",
    @SerialName("author_user_id") val authorUserId: String,
    val url: String,
    val description: String? = null,
    @SerialName("ai_status") val aiStatus: String,
    val status: String,
    @SerialName("reports_count") val reportsCount: Int,
    @SerialName("is_ad") val isAd: Boolean,
    @SerialName("views_count") val viewsCount: Int,
    @SerialName("likes_count") val likesCount: Int,
    @SerialName("shares_count") val sharesCount: Int,
    @SerialName("created_at") val createdAt: String,
    @SerialName("liked_by_me") val likedByMe: Boolean = false,
    @SerialName("comments_count") val commentsCount: Int = 0,
)

@Serializable
data class JoinChallengeRequestDto(@SerialName("challenge_type") val challengeType: String)

@Serializable
data class CommentDto(
    val id: String,
    @SerialName("video_id") val videoId: String,
    @SerialName("user_id") val userId: String,
    val username: String,
    val text: String,
    @SerialName("created_at") val createdAt: String,
)

@Serializable
data class CreateCommentRequestDto(val text: String)
