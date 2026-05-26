package com.challengehub.mobile.core.network

import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.POST
import retrofit2.http.Path

interface ChallengeHubApi {
    @POST("mobile/auth/login")
    suspend fun login(@Body body: LoginRequestDto): TokenDto

    @POST("mobile/auth/register")
    suspend fun register(@Body body: RegisterRequestDto): TokenDto

    @GET("mobile/auth/me")
    suspend fun me(@Header("Authorization") authorization: String): MobileUserDto

    @GET("mobile/feed")
    suspend fun feed(): List<VideoDto>

    @GET("mobile/challenges")
    suspend fun challenges(): List<ChallengeDto>

    @POST("mobile/challenges/{id}/join")
    suspend fun joinChallenge(
        @Header("Authorization") authorization: String,
        @Path("id") id: String,
        @Body body: JoinChallengeRequestDto,
    )

    @POST("mobile/videos/{id}/like")
    suspend fun likeVideo(
        @Header("Authorization") authorization: String,
        @Path("id") id: String,
    ): VideoDto

    @DELETE("mobile/videos/{id}/like")
    suspend fun unlikeVideo(
        @Header("Authorization") authorization: String,
        @Path("id") id: String,
    ): VideoDto

    @GET("mobile/videos/{id}/comments")
    suspend fun comments(@Path("id") id: String): List<CommentDto>

    @POST("mobile/videos/{id}/comments")
    suspend fun addComment(
        @Header("Authorization") authorization: String,
        @Path("id") id: String,
        @Body body: CreateCommentRequestDto,
    ): CommentDto
}
