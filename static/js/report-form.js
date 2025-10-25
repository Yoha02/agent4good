// Report Form Handling
document.addEventListener('DOMContentLoaded', function() {
    const reportForm = document.getElementById('reportForm');
    const uploadZone = document.getElementById('uploadZone');
    const photoInput = document.getElementById('photoInput');
    const photoPreview = document.getElementById('photoPreview');
    const reportTypeInputs = document.querySelectorAll('input[name="reportType"]');
    const specificTypeSelect = document.getElementById('specificType');
    const MAX_FILES = 10;
    const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
    
    let selectedFiles = [];

    // Report type specific options
    const specificTypes = {
        health: [
            'Respiratory issues (coughing, difficulty breathing)',
            'Allergic reactions',
            'Skin irritation',
            'Nausea or vomiting',
            'Headaches or dizziness',
            'Illness outbreak',
            'Other health symptoms'
        ],
        environmental: [
            'Poor air quality (smoke, odor, haze)',
            'Water contamination',
            'Chemical spill or leak',
            'Hazardous waste',
            'Noise pollution',
            'Illegal dumping',
            'Other environmental issue'
        ],
        weather: [
            'Severe thunderstorm',
            'Flooding',
            'Extreme heat',
            'Extreme cold',
            'High winds',
            'Hail or ice',
            'Other weather event'
        ],
        emergency: [
            'Fire',
            'Chemical emergency',
            'Infrastructure damage',
            'Gas leak',
            'Power outage affecting health',
            'Other emergency'
        ]
    };

    // Update specific type options when report type changes
    reportTypeInputs.forEach(input => {
        input.addEventListener('change', function() {
            const selectedType = this.value;
            specificTypeSelect.innerHTML = '<option value="">Select issue type</option>';
            
            if (specificTypes[selectedType]) {
                specificTypes[selectedType].forEach(type => {
                    const option = document.createElement('option');
                    option.value = type;
                    option.textContent = type;
                    specificTypeSelect.appendChild(option);
                });
            }
            
            // Update border color on selected report type card
            document.querySelectorAll('.report-type-option div').forEach(div => {
                div.classList.remove('border-blue-500', 'bg-blue-50', 'border-green-500', 'bg-green-50', 'border-red-500', 'bg-red-50');
            });
            this.parentElement.querySelector('div').classList.add('border-blue-500', 'bg-blue-50');
        });
    });

    // Handle severity selection visual feedback
    document.querySelectorAll('.severity-option input').forEach(input => {
        input.addEventListener('change', function() {
            document.querySelectorAll('.severity-option div').forEach(div => {
                div.classList.remove('border-green-500', 'border-yellow-500', 'border-red-500', 'border-red-600');
            });
            this.parentElement.querySelector('div').classList.add('border-blue-500');
        });
    });

    // File upload handling
    uploadZone.addEventListener('click', () => photoInput.click());
    
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    });
    
    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('dragover');
    });
    
    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        handleFiles(e.dataTransfer.files);
    });
    
    photoInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });

    function handleFiles(files) {
        const newFiles = Array.from(files);
        
        // Check total file count
        if (selectedFiles.length + newFiles.length > MAX_FILES) {
            alert(`You can only upload up to ${MAX_FILES} files. Currently selected: ${selectedFiles.length}`);
            return;
        }
        
        // Validate and add files
        newFiles.forEach(file => {
            // Check file size
            if (file.size > MAX_FILE_SIZE) {
                alert(`File "${file.name}" is too large. Maximum size is 50MB.`);
                return;
            }
            
            // Check file type
            const isImage = file.type.startsWith('image/');
            const isVideo = file.type.startsWith('video/');
            
            if (!isImage && !isVideo) {
                alert(`File "${file.name}" is not a valid image or video file.`);
                return;
            }
            
            selectedFiles.push(file);
        });
        
        updatePreview();
    }

    function updatePreview() {
        if (selectedFiles.length === 0) {
            photoPreview.classList.add('hidden');
            return;
        }
        
        photoPreview.classList.remove('hidden');
        photoPreview.innerHTML = '';
        
        selectedFiles.forEach((file, index) => {
            const previewDiv = document.createElement('div');
            previewDiv.className = 'image-preview relative';
            
            const isVideo = file.type.startsWith('video/');
            
            if (isVideo) {
                const video = document.createElement('video');
                video.className = 'w-full h-full object-cover';
                video.src = URL.createObjectURL(file);
                video.controls = false;
                previewDiv.appendChild(video);
                
                const videoIcon = document.createElement('div');
                videoIcon.className = 'absolute inset-0 flex items-center justify-center bg-black bg-opacity-30';
                videoIcon.innerHTML = '<i class="fas fa-play-circle text-white text-4xl"></i>';
                previewDiv.appendChild(videoIcon);
            } else {
                const img = document.createElement('img');
                img.src = URL.createObjectURL(file);
                img.alt = file.name;
                previewDiv.appendChild(img);
            }
            
            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.className = 'remove-image';
            removeBtn.innerHTML = '<i class="fas fa-times"></i>';
            removeBtn.onclick = () => removeFile(index);
            previewDiv.appendChild(removeBtn);
            
            const fileName = document.createElement('p');
            fileName.className = 'text-xs text-gray-600 mt-2 truncate';
            fileName.textContent = file.name;
            previewDiv.appendChild(fileName);
            
            photoPreview.appendChild(previewDiv);
        });
    }

    function removeFile(index) {
        selectedFiles.splice(index, 1);
        updatePreview();
    }

    // Form submission
    reportForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Show loading state
        const submitBtn = reportForm.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-3"></i>Submitting...';
        submitBtn.disabled = true;
        
        // Collect form data
        const formData = new FormData(reportForm);
        
        // Add files to form data
        selectedFiles.forEach((file, index) => {
            formData.append('media[]', file);
        });
        
        try {
            // Submit to backend
            const response = await fetch('/api/submit-report', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                console.log('Report submitted successfully:', result.report_id);
                
                // Show success modal
                document.getElementById('successModal').classList.remove('hidden');
                
                // Reset form
                reportForm.reset();
                selectedFiles = [];
                updatePreview();
            } else {
                alert('Error submitting report: ' + result.error);
            }
        } catch (error) {
            console.error('Error submitting report:', error);
            alert('Failed to submit report. Please try again.');
        } finally {
            // Restore button
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    });

    // Close success modal
    document.getElementById('closeModal').addEventListener('click', function() {
        document.getElementById('successModal').classList.add('hidden');
    });

    // Mobile menu toggle
    window.toggleMobileMenu = function() {
        const mobileMenu = document.getElementById('mobileMenu');
        mobileMenu.classList.toggle('hidden');
    };
    
    // Generate UUID
    function generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
});
