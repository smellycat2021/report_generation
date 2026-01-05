// --- DOM Element References ---
const fileInput = document.getElementById('fileInput');
const dropArea = document.getElementById('dropArea');
const uploadedFilesList = document.getElementById('uploadedFilesList');
const generateButton = document.getElementById('generateButton');
const statusMessage = document.getElementById('statusMessage');
const progressBarContainer = document.getElementById('progressBarContainer');
const progressBar = document.getElementById('progressBar');
const downloadLinkArea = document.getElementById('downloadLinkArea');
const downloadButton = document.getElementById('downloadButton');
const reportTypeDescription = document.getElementById('reportTypeDescription');

let selectedFiles = [];
let currentReportType = 'board';

// --- INITIALIZATION AND EVENT LISTENERS ---
document.addEventListener('DOMContentLoaded', () => {
    // 1. Link file input to drop area click
    dropArea.addEventListener('click', () => fileInput.click());

    // 2. Handle files selected via input dialog
    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });

    // 3. Link button to generation function
    generateButton.addEventListener('click', handleReportGeneration);

    // 4. Basic Drag/Drop events (prevent browser default)
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });

    dropArea.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        if (dt) handleFiles(dt.files);
    }, false);

    // 5. Handle report type selection
    const reportTypeRadios = document.querySelectorAll('input[name="reportType"]');
    reportTypeRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            currentReportType = e.target.value;
            updateUIForReportType();
        });
    });
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function updateUIForReportType() {
    if (currentReportType === 'board') {
        generateButton.textContent = '生成报表 Generate Board Report';
        reportTypeDescription.textContent = '上传制造商Excel文件并生成合并汇总报表 | Upload manufacturer Excel files and generate a consolidated summary report.';
        fileInput.setAttribute('multiple', 'true');
    } else {
        generateButton.textContent = '生成报价单 Generate Quotation Sheet';
        reportTypeDescription.textContent = '上传采购订单Excel文件并生成报价单 | Upload purchase order Excel file and generate quotation sheet.';
        fileInput.removeAttribute('multiple');
    }
    // Clear selected files when switching types
    selectedFiles = [];
    displayFiles([]);
}

function handleFiles(files) {
    if (!files) return;

    selectedFiles = Array.from(files).filter(file =>
        file.name.endsWith('.xlsx') || file.name.endsWith('.xls')
    );
    displayFiles(selectedFiles);
}

function displayFiles(files) {
    uploadedFilesList.innerHTML = '';

    if (files.length === 0) {
        uploadedFilesList.innerHTML = '<li>No valid files selected.</li>';
        generateButton.disabled = true;
        return;
    }

    files.forEach(file => {
        const li = document.createElement('li');
        li.textContent = `${file.name} (${(file.size / 1024).toFixed(2)} KB)`;
        uploadedFilesList.appendChild(li);
    });
    generateButton.disabled = false;
}

// --- API INTERACTION AND UI STATE MANAGEMENT ---
function setProcessingState(message, isProcessing, progress) {
    generateButton.disabled = isProcessing || selectedFiles.length === 0;
    statusMessage.textContent = message;

    if (isProcessing) {
        progressBarContainer.classList.remove('hidden');
        downloadLinkArea.classList.add('hidden');
        // Update progress bar width and text
        progressBar.style.width = `${progress}%`;
        progressBar.textContent = `${progress}%`;
    } else {
        progressBarContainer.classList.add('hidden');
    }
}

async function handleReportGeneration() {
    if (selectedFiles.length === 0) return;

    if (currentReportType === 'quotation') {
        await handleQuotationGeneration();
    } else {
        await handleBoardReportGeneration();
    }
}

async function handleQuotationGeneration() {
    // 1. START PROCESSING (UI State)
    setProcessingState('Generating quotation sheet...', true, 30);
    downloadLinkArea.classList.add('hidden');

    try {
        const formData = new FormData();
        formData.append('file', selectedFiles[0]); // Quotation uses single file

        const generateResponse = await fetch('/api/quotation/generate', {
            method: 'POST',
            body: formData
        });

        if (!generateResponse.ok) throw new Error(`Generation failed (${generateResponse.status})`);

        const quotationData = await generateResponse.json();

        // SUCCESS (UI State)
        const matchInfo = quotationData.match_stats ?
            ` | Matched: ${quotationData.match_stats.matched_items}/${quotationData.match_stats.total_items} (${quotationData.match_stats.match_rate}%)` :
            '';
        setProcessingState(`✅ Quotation complete!${matchInfo}`, false, 100);
        downloadButton.href = quotationData.download_url;
        downloadLinkArea.classList.remove('hidden');

    } catch (error) {
        setProcessingState(`Error: Quotation generation failed. ${error.message}`, false, 0);
    } finally {
        // Reset files list after processing
        selectedFiles = [];
        uploadedFilesList.innerHTML = '<li>Ready for new upload.</li>';
        generateButton.disabled = true;
    }
}

async function handleBoardReportGeneration() {
    // 1. START PROCESSING (UI State)
    setProcessingState('Step 1/2: Uploading files...', true, 10);
    downloadLinkArea.classList.add('hidden');

    let uploadedFilePaths = [];

    // --- STEP 1: UPLOAD FILES ---
    try {
        const formData = new FormData();
        selectedFiles.forEach(file => formData.append('files[]', file));

        const uploadResponse = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        if (!uploadResponse.ok) throw new Error(`Upload failed (${uploadResponse.status})`);

        const uploadData = await uploadResponse.json();
        uploadedFilePaths = uploadData.file_paths;

    } catch (error) {
        setProcessingState(`Error: Upload failed. ${error.message}`, false, 0);
        return;
    }

    // --- STEP 2: GENERATE REPORT ---
    setProcessingState('Step 2/2: Processing data and generating report...', true, 50);

    try {
        const dateRange = 'Placeholder_Date_Range'; // Replace with actual input value

        const generateResponse = await fetch('/api/report/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                file_paths: uploadedFilePaths,
                params: { date_range: dateRange }
            })
        });

        if (!generateResponse.ok) throw new Error(`Generation failed (${generateResponse.status})`);

        const reportData = await generateResponse.json();

        // 3. SUCCESS (UI State)
        setProcessingState(`✅ Report complete! ${reportData.report_id}`, false, 100);
        downloadButton.href = reportData.download_url;
        downloadLinkArea.classList.remove('hidden');

    } catch (error) {
        setProcessingState(`Error: Report generation failed. ${error.message}`, false, 0);
    } finally {
        // Reset files list after processing
        selectedFiles = [];
        uploadedFilesList.innerHTML = '<li>Ready for new upload.</li>';
        generateButton.disabled = true;
    }
}

export {};
