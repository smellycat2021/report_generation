// interfaces.ts

// Define the API response structure for file upload
export interface UploadResponse {
    message: string;
    file_paths: string[];
}

// Define the API response structure for report generation
export interface ReportGenerationResponse {
    report_id: string;
    status: string;
    download_url: string;
}

// Any other core data models go here...