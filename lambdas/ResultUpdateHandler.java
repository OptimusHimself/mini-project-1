package com.example;

import com.aliyun.fc.runtime.Context;
import com.aliyun.fc.runtime.StreamRequestHandler;
import com.google.gson.Gson;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.google.gson.JsonSyntaxException;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.stream.Collectors;

public class ResultUpdateHandler implements StreamRequestHandler {
    
    private static final Gson gson = new Gson();
    
    @Override
    public void handleRequest(InputStream input, OutputStream output, Context context) throws java.io.IOException {
        context.getLogger().info("Result Update Function triggered");
        
        // 1. 读取原始请求体
        String requestBody = new BufferedReader(new InputStreamReader(input))
            .lines().collect(Collectors.joining("\n"));
        context.getLogger().info("Raw received: " + requestBody);
        
        // 2. 解析阿里云网关包装格式
        int submissionId = 0;
        String status = null;
        String note = null;
        
        try {
            JsonObject wrapper = JsonParser.parseString(requestBody).getAsJsonObject();
            
            if (wrapper.has("body")) {
                // 阿里云网关包装格式
                String bodyStr = wrapper.get("body").getAsString();
                context.getLogger().info("Extracted body: " + bodyStr);
                JsonObject bodyJson = JsonParser.parseString(bodyStr).getAsJsonObject();
                
                if (bodyJson.has("submission_id")) {
                    try {
                        submissionId = bodyJson.get("submission_id").getAsInt();
                    } catch (NumberFormatException e) {
                        submissionId = Integer.parseInt(bodyJson.get("submission_id").getAsString());
                    }
                }
                status = bodyJson.has("status") ? bodyJson.get("status").getAsString() : null;
                note = bodyJson.has("note") ? bodyJson.get("note").getAsString() : null;
            } else {
                // 直接是业务数据（控制台测试时）
                if (wrapper.has("submission_id")) {
                    try {
                        submissionId = wrapper.get("submission_id").getAsInt();
                    } catch (NumberFormatException e) {
                        submissionId = Integer.parseInt(wrapper.get("submission_id").getAsString());
                    }
                }
                status = wrapper.has("status") ? wrapper.get("status").getAsString() : null;
                note = wrapper.has("note") ? wrapper.get("note").getAsString() : null;
            }
        } catch (JsonSyntaxException e) {
            context.getLogger().error("Failed to parse JSON: " + e.getMessage());
        }
        
        context.getLogger().info("Parsed - submissionId: " + submissionId);
        context.getLogger().info("Parsed - status: " + status);
        context.getLogger().info("Parsed - note: " + note);
        
        // 3. 验证必需字段
        if (submissionId <= 0 || status == null) {
            JsonObject errorResponse = new JsonObject();
            errorResponse.addProperty("error", "Missing submission_id or status");
            output.write(gson.toJson(errorResponse).getBytes());
            return;
        }
        
        // 4. 调用 Data Service
        String dataServiceBaseUrl = System.getenv().getOrDefault("DATA_SERVICE_URL",
            "http://54.252.166.148:5002");
        String dataServiceUrl = dataServiceBaseUrl + "/update/" + submissionId;
        
        context.getLogger().info("Calling Data Service at: " + dataServiceUrl);
        
        JsonObject updatePayload = new JsonObject();
        updatePayload.addProperty("status", status);
        updatePayload.addProperty("note", note == null ? "" : note);
        
        int dataServiceResponse = callDataService(dataServiceUrl, gson.toJson(updatePayload), context);
        
        // 5. 返回响应
        JsonObject responseJson = new JsonObject();
        responseJson.addProperty("message", "Result updated successfully");
        responseJson.addProperty("submission_id", submissionId);
        responseJson.addProperty("status", status);
        responseJson.addProperty("data_service_response_code", dataServiceResponse);
        
        output.write(gson.toJson(responseJson).getBytes());
        context.getLogger().info("Response sent: " + gson.toJson(responseJson));
    }
    
    private int callDataService(String urlString, String payload, Context context) {
        HttpURLConnection conn = null;
        try {
            URL url = new URL(urlString);
            conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("PUT");
            conn.setRequestProperty("Content-Type", "application/json");
            conn.setDoOutput(true);
            conn.setConnectTimeout(30000);
            conn.setReadTimeout(30000);
            
            try (OutputStreamWriter writer = new OutputStreamWriter(conn.getOutputStream(), "UTF-8")) {
                writer.write(payload);
                writer.flush();
            }
            
            int responseCode = conn.getResponseCode();
            context.getLogger().info("Data Service response code: " + responseCode);
            return responseCode;
        } catch (Exception e) {
            context.getLogger().error("Failed to call Data Service: " + e.getMessage());
            return 500;
        } finally {
            if (conn != null) {
                conn.disconnect();
            }
        }
    }
}