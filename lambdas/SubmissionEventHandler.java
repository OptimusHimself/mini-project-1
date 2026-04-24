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

public class SubmissionEventHandler implements StreamRequestHandler {
    
    private static final Gson gson = new Gson();
    
    @Override
    public void handleRequest(InputStream input, OutputStream output, Context context) throws java.io.IOException {
        context.getLogger().info("Submission Event Function triggered");
        
        // 1. 读取原始请求体
        String requestBody = new BufferedReader(new InputStreamReader(input))
            .lines().collect(Collectors.joining("\n"));
        context.getLogger().info("Raw request body: " + requestBody);
        
        // 2. 解析阿里云 HTTP 触发器网关包装格式
        int submissionId = 0;
        String title = null;
        String description = null;
        String posterFilename = null;
        
        try {
            JsonObject wrapper = JsonParser.parseString(requestBody).getAsJsonObject();
            
            // 检查是否是阿里云网关包装格式（包含 body 字段）
            if (wrapper.has("body")) {
                String bodyStr = wrapper.get("body").getAsString();
                context.getLogger().info("Extracted body: " + bodyStr);
                
                JsonObject bodyJson = JsonParser.parseString(bodyStr).getAsJsonObject();
                
                // ========== 格式A：标准格式 ==========
                if (bodyJson.has("submission_id")) {
                    if (bodyJson.get("submission_id").isJsonPrimitive()) {
                        try {
                            submissionId = bodyJson.get("submission_id").getAsInt();
                        } catch (NumberFormatException e) {
                            submissionId = Integer.parseInt(bodyJson.get("submission_id").getAsString());
                        }
                    }
                    title = bodyJson.has("title") ? bodyJson.get("title").getAsString() : null;
                    description = bodyJson.has("description") ? bodyJson.get("description").getAsString() : null;
                    posterFilename = bodyJson.has("poster_filename") ? bodyJson.get("poster_filename").getAsString() : null;
                    
                    context.getLogger().info("Using standard format (submission_id) - from body");
                    
                // ========== 格式B：组员格式（record_id + data 嵌套） ==========
                } else if (bodyJson.has("record_id") && bodyJson.has("data")) {
                    if (bodyJson.get("record_id").isJsonPrimitive()) {
                        try {
                            submissionId = bodyJson.get("record_id").getAsInt();
                        } catch (NumberFormatException e) {
                            submissionId = Integer.parseInt(bodyJson.get("record_id").getAsString());
                        }
                    }
                    
                    JsonObject dataObj = bodyJson.getAsJsonObject("data");
                    if (dataObj != null) {
                        title = dataObj.has("title") ? dataObj.get("title").getAsString() : null;
                        description = dataObj.has("description") ? dataObj.get("description").getAsString() : null;
                        if (dataObj.has("poster_filename")) {
                            posterFilename = dataObj.get("poster_filename").getAsString();
                        } else if (dataObj.has("filename")) {
                            posterFilename = dataObj.get("filename").getAsString();
                        }
                    }
                    
                    context.getLogger().info("Using team member format (record_id + data) - from body");
                }
            } else {
                // ========== 直接是业务数据（控制台直接测试时） ==========
                
                // 格式A：标准格式
                if (wrapper.has("submission_id")) {
                    if (wrapper.get("submission_id").isJsonPrimitive()) {
                        try {
                            submissionId = wrapper.get("submission_id").getAsInt();
                        } catch (NumberFormatException e) {
                            submissionId = Integer.parseInt(wrapper.get("submission_id").getAsString());
                        }
                    }
                    title = wrapper.has("title") ? wrapper.get("title").getAsString() : null;
                    description = wrapper.has("description") ? wrapper.get("description").getAsString() : null;
                    posterFilename = wrapper.has("poster_filename") ? wrapper.get("poster_filename").getAsString() : null;
                    
                    context.getLogger().info("Using standard format (submission_id) - direct");
                    
                // 格式B：组员格式（控制台直接测试时）
                } else if (wrapper.has("record_id") && wrapper.has("data")) {
                    if (wrapper.get("record_id").isJsonPrimitive()) {
                        try {
                            submissionId = wrapper.get("record_id").getAsInt();
                        } catch (NumberFormatException e) {
                            submissionId = Integer.parseInt(wrapper.get("record_id").getAsString());
                        }
                    }
                    
                    JsonObject dataObj = wrapper.getAsJsonObject("data");
                    if (dataObj != null) {
                        title = dataObj.has("title") ? dataObj.get("title").getAsString() : null;
                        description = dataObj.has("description") ? dataObj.get("description").getAsString() : null;
                        if (dataObj.has("poster_filename")) {
                            posterFilename = dataObj.get("poster_filename").getAsString();
                        } else if (dataObj.has("filename")) {
                            posterFilename = dataObj.get("filename").getAsString();
                        }
                    }
                    
                    context.getLogger().info("Using team member format (record_id + data) - direct");
                }
            }
        } catch (JsonSyntaxException e) {
            context.getLogger().error("Failed to parse JSON: " + e.getMessage());
        }
        
        context.getLogger().info("Parsed - submissionId: " + submissionId);
        context.getLogger().info("Parsed - title: " + title);
        context.getLogger().info("Parsed - description: " + description);
        context.getLogger().info("Parsed - posterFilename: " + posterFilename);
        
        // 3. 验证必需字段
        if (submissionId <= 0) {
            JsonObject errorResponse = new JsonObject();
            errorResponse.addProperty("error", "Missing or invalid submission_id");
            output.write(gson.toJson(errorResponse).getBytes());
            return;
        }
        
        // 4. 验证业务必需字段（可选，仅记录警告）
        if (title == null || title.isEmpty() || description == null || description.isEmpty() || posterFilename == null || posterFilename.isEmpty()) {
            context.getLogger().warn("Missing business fields - title:" + (title == null) + 
                                     ", description:" + (description == null) + 
                                     ", posterFilename:" + (posterFilename == null));
        }
        
        // 5. 构建发送给 Processing Function 的 payload（统一转换为标准格式）
        JsonObject payloadJson = new JsonObject();
        payloadJson.addProperty("submission_id", submissionId);
        payloadJson.addProperty("title", title == null ? "" : title);
        payloadJson.addProperty("description", description == null ? "" : description);
        payloadJson.addProperty("poster_filename", posterFilename == null ? "" : posterFilename);
        
        String payload = gson.toJson(payloadJson);
        context.getLogger().info("Payload to processing: " + payload);
        
        // 6. 获取 Processing Function URL
        String processingUrl = System.getenv().getOrDefault("PROCESSING_FUNCTION_URL", 
            "https://processfunction-csckxymeyv.cn-hangzhou.fcapp.run");
        
        // 7. 调用 Processing Function
        String processingResult = callFunction(processingUrl, payload, context);
        
        // 8. 构建并返回响应
        JsonObject responseJson = new JsonObject();
        responseJson.addProperty("message", "Processing triggered");
        responseJson.addProperty("submission_id", submissionId);
        
        try {
            JsonObject resultJson = JsonParser.parseString(processingResult).getAsJsonObject();
            responseJson.add("result", resultJson);
        } catch (JsonSyntaxException e) {
            responseJson.addProperty("result", processingResult);
        }
        
        output.write(gson.toJson(responseJson).getBytes());
        context.getLogger().info("Response sent: " + gson.toJson(responseJson));
    }
    
    private String callFunction(String urlString, String payload, Context context) {
        HttpURLConnection conn = null;
        try {
            URL url = new URL(urlString);
            conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("POST");
            conn.setRequestProperty("Content-Type", "application/json");
            conn.setDoOutput(true);
            conn.setConnectTimeout(30000);
            conn.setReadTimeout(30000);
            
            try (OutputStreamWriter writer = new OutputStreamWriter(conn.getOutputStream(), "UTF-8")) {
                writer.write(payload);
                writer.flush();
            }
            
            int responseCode = conn.getResponseCode();
            context.getLogger().info("Called processing function, response code: " + responseCode);
            
            StringBuilder response = new StringBuilder();
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(conn.getInputStream(), "UTF-8"))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    response.append(line);
                }
            }
            
            return response.toString();
            
        } catch (Exception e) {
            context.getLogger().error("Failed to call processing function: " + e.getMessage());
            return "{\"error\":\"Failed to trigger processing\"}";
        } finally {
            if (conn != null) {
                conn.disconnect();
            }
        }
    }
}