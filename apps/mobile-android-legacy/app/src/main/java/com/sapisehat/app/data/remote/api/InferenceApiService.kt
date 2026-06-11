package com.sapisehat.app.data.remote.api

import okhttp3.MultipartBody
import retrofit2.http.GET
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.Part
import com.sapisehat.app.data.remote.dto.HealthResponseDto
import com.sapisehat.app.data.remote.dto.PredictResponseDto

interface InferenceApiService {
    @Multipart
    @POST("api/predict")
    suspend fun predict(@Part image: MultipartBody.Part): PredictResponseDto

    @GET("api/health")
    suspend fun health(): HealthResponseDto
}
