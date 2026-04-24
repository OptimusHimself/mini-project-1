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

public class ProcessingHandler implements StreamRequestHandler {
    
    private static final Gson gson = new Gson();
    
    @Override
    public void handleRequest(InputStream input, OutputStream output, Context context) throws java.io.IOException {
        context.getLogger().info("Processing Function triggered");
        
        // 1. 读取原始请求体
        String requestBody = new BufferedReader(new InputStreamReader(input))
            .lines().collect(Collectors.joining("\n"));
        context.getLogger().info("Raw received: " + requestBody);
        
        // 2. 解析数据
        int submissionId = 0;
        String title = null;
        String description = null;
        String posterFilename = null;
        
        try {
            JsonObject wrapper = JsonParser.parseString(requestBody).getAsJsonObject();
            
            if (wrapper.has("body")) {
                String bodyStr = wrapper.get("body").getAsString();
                context.getLogger().info("Extracted body: " + bodyStr);
                JsonObject bodyJson = JsonParser.parseString(bodyStr).getAsJsonObject();
                
                if (bodyJson.has("submission_id")) {
                    if (bodyJson.get("submission_id").isJsonPrimitive()) {
                        try {
                            submissionId = bodyJson.get("submission_id").getAsInt();
                        } catch (NumberFormatException e) {
                            submissionId = Integer.parseInt(bodyJson.get("submission_id").getAsString());
                        }
                    }
                }
                title = bodyJson.has("title") ? bodyJson.get("title").getAsString() : null;
                description = bodyJson.has("description") ? bodyJson.get("description").getAsString() : null;
                posterFilename = bodyJson.has("poster_filename") ? bodyJson.get("poster_filename").getAsString() : null;
            } else {
                if (wrapper.has("submission_id")) {
                    if (wrapper.get("submission_id").isJsonPrimitive()) {
                        try {
                            submissionId = wrapper.get("submission_id").getAsInt();
                        } catch (NumberFormatException e) {
                            submissionId = Integer.parseInt(wrapper.get("submission_id").getAsString());
                        }
                    }
                }
                title = wrapper.has("title") ? wrapper.get("title").getAsString() : null;
                description = wrapper.has("description") ? wrapper.get("description").getAsString() : null;
                posterFilename = wrapper.has("poster_filename") ? wrapper.get("poster_filename").getAsString() : null;
            }
        } catch (JsonSyntaxException e) {
            context.getLogger().error("Failed to parse JSON: " + e.getMessage());
        }
        
        context.getLogger().info("Parsed - submissionId: " + submissionId);
        context.getLogger().info("Parsed - title: " + title);
        context.getLogger().info("Parsed - description: " + description);
        context.getLogger().info("Parsed - posterFilename: " + posterFilename);
        
        // 3. 业务规则实现
        String finalStatus;
        String note;
        
        boolean hasAllRequired = (title != null && !title.trim().isEmpty()) &&
                                 (description != null && !description.trim().isEmpty()) &&
                                 (posterFilename != null && !posterFilename.trim().isEmpty());
        
        if (!hasAllRequired) {
            finalStatus = "INCOMPLETE";
            note = "Missing required fields. Please provide title, description, and poster filename.";
        } else {
            boolean isValidDescription = description.trim().length() >= 30;
            String filenameLower = posterFilename.trim().toLowerCase();
            boolean isValidFilename = filenameLower.endsWith(".jpg") || 
                                      filenameLower.endsWith(".jpeg") || 
                                      filenameLower.endsWith(".png");
            
            if (!isValidDescription || !isValidFilename) {
                finalStatus = "NEEDS REVISION";
                if (!isValidDescription && !isValidFilename) {
                    note = "Description must be at least 30 characters and poster filename must end with .jpg, .jpeg, or .png.";
                } else if (!isValidDescription) {
                    note = "Description must be at least 30 characters.";
                } else {
                    note = "Poster filename must end with .jpg, .jpeg, or .png.";
                }
            } else {
                finalStatus = "READY";
                note = "All checks passed. Poster is ready for sharing.";
            }
        }
        
        context.getLogger().info("Result - Status: " + finalStatus + ", Note: " + note);
        
        // 4. 调用 Result Update Function
        String updateUrl = System.getenv().getOrDefault("RESULT_UPDATE_FUNCTION_URL",
            "https://result-function-rrhufjmcil.cn-hangzhou.fcapp.run");
        context.getLogger().info("Calling Result Update Function at: " + updateUrl);
        
        JsonObject updatePayload = new JsonObject();
        updatePayload.addProperty("submission_id", submissionId);  // 整数类型
        updatePayload.addProperty("status", finalStatus);
        updatePayload.addProperty("note", note);
        
        String updateResult = callFunction(updateUrl, gson.toJson(updatePayload), context);
        context.getLogger().info("Result Update Function response: " + updateResult);
        
        // 5. 返回结果
        JsonObject responseJson = new JsonObject();
        responseJson.addProperty("submission_id", submissionId);
        responseJson.addProperty("status", finalStatus);
        responseJson.addProperty("note", note);
        
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
            context.getLogger().info("Called update function, response code: " + responseCode);
            
            StringBuilder response = new StringBuilder();
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(conn.getInputStream(), "UTF-8"))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    response.append(line);
                }
            }
            
            return response.toString();
            
        } catch (Exception e) {
            context.getLogger().error("Failed to call update function: " + e.getMessage());
            return "{\"error\":\"Failed to update result\"}";
        } finally {
            if (conn != null) {
                conn.disconnect();
            }
        }
    }
}