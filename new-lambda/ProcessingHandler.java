package com.example;

import com.aliyun.fc.runtime.Context;
import com.aliyun.fc.runtime.StreamRequestHandler;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.stream.Collectors;

public class ProcessingHandler implements StreamRequestHandler {

    @Override
    public void handleRequest(InputStream input, OutputStream output, Context context) throws java.io.IOException {
        context.getLogger().info("Processing Function triggered");

        String requestBody = new BufferedReader(new InputStreamReader(input))
                .lines().collect(Collectors.joining("\n"));
        context.getLogger().info("Received: " + requestBody);

        String submissionId = extractJsonValue(requestBody, "submission_id");
        String title = extractJsonValue(requestBody, "title");
        String description = extractJsonValue(requestBody, "description");
        String posterFilename = extractJsonValue(requestBody, "poster_filename");

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

        String response = "{\"submission_id\":\"" + submissionId +
                          "\",\"status\":\"" + finalStatus +
                          "\",\"note\":\"" + escapeJson(note) + "\"}";
        output.write(response.getBytes());
    }

    private String extractJsonValue(String json, String key) {
        String searchKey = "\"" + key + "\":";
        int keyIndex = json.indexOf(searchKey);
        if (keyIndex == -1) return null;

        int startQuote = json.indexOf("\"", keyIndex + searchKey.length());
        if (startQuote == -1) return null;

        int endQuote = json.indexOf("\"", startQuote + 1);
        if (endQuote == -1) return null;

        return json.substring(startQuote + 1, endQuote);
    }

    private String escapeJson(String str) {
        if (str == null) return "";
        return str.replace("\\", "\\\\").replace("\"", "\\\"");
    }
}