// Report Form JavaScript
class ReportForm {
    constructor() {
        this.maxPhotos = 3;
        this.uploadedPhotos = [];
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initAnimations();
        this.loadSpecificTypes();
    }

    setupEventListeners() {
        // Report type selection
        document.querySelectorAll('input[name="reportType"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.handleReportTypeChange(e.target.value);
                this.updateSpecificTypes(e.target.value);
            });
        });

        // Severity selection
        document.querySelectorAll('input[name="severity"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.handleSeverityChange(e.target.value);
            });
        });

        // Photo upload
        const uploadZone = document.getElementById('uploadZone');
        const photoInput = document.getElementById('photoInput');

        uploadZone.addEventListener('click', () => photoInput.click());
        uploadZone.addEventListener('dragover', this.handleDragOver);
        uploadZone.addEventListener('dragleave', this.handleDragLeave);
        uploadZone.addEventListener('drop', this.handleDrop.bind(this));
        
        photoInput.addEventListener('change', (e) => {
            this.handleFileSelect(e.target.files);
        });

        // Form submission
        document.getElementById('reportForm').addEventListener('submit', this.handleSubmit.bind(this));

        // Anonymous checkbox
        document.getElementById('anonymous').addEventListener('change', (e) => {
            this.toggleContactFields(e.target.checked);
        });

        // Modal close
        document.getElementById('closeModal').addEventListener('click', this.closeSuccessModal);

        // Auto-fill location based on zip code
        document.querySelector('input[name="zipCode"]').addEventListener('blur', this.autoFillLocation.bind(this));
    }

    initAnimations() {
        // Animate form sections on scroll
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    anime({
                        targets: entry.target,
                        translateY: [30, 0],
                        opacity: [0, 1],
                        duration: 600,
                        easing: 'easeOutCubic',
                        delay: 200
                    });
                }
            });
        }, { threshold: 0.1 });

        document.querySelectorAll('.form-section').forEach(section => {
            observer.observe(section);
        });

        // Floating elements animation
        anime({
            targets: '.floating-element',
            translateY: [-10, 10],
            rotate: [-5, 5],
            duration: 3000,
            direction: 'alternate',
            loop: true,
            easing: 'easeInOutSine',
            delay: anime.stagger(500)
        });
    }

    handleReportTypeChange(type) {
        // Update visual selection
        document.querySelectorAll('.report-type-option').forEach(option => {
            const div = option.querySelector('div');
            const input = option.querySelector('input');
            
            if (input.value === type) {
                div.classList.add('border-blue-500', 'bg-blue-50');
                div.classList.remove('border-gray-200');
            } else {
                div.classList.remove('border-blue-500', 'bg-blue-50', 'border-green-400', 'bg-green-50', 'border-red-400', 'bg-red-50');
                div.classList.add('border-gray-200');
            }
        });

        // Add specific styling based on type
        const selectedOption = document.querySelector(`input[name="reportType"][value="${type}"]`).closest('.report-type-option');
        const div = selectedOption.querySelector('div');
        
        switch(type) {
            case 'health':
                div.classList.add('border-red-400', 'bg-red-50');
                break;
            case 'environmental':
                div.classList.add('border-green-400', 'bg-green-50');
                break;
            case 'weather':
                div.classList.add('border-blue-400', 'bg-blue-50');
                break;
            case 'emergency':
                div.classList.add('border-red-600', 'bg-red-50');
                break;
        }
    }

    handleSeverityChange(severity) {
        document.querySelectorAll('.severity-option').forEach(option => {
            const div = option.querySelector('div');
            const input = option.querySelector('input');
            
            if (input.value === severity) {
                switch(severity) {
                    case 'low':
                        div.classList.add('border-green-400', 'bg-green-50');
                        break;
                    case 'moderate':
                        div.classList.add('border-yellow-400', 'bg-yellow-50');
                        break;
                    case 'high':
                        div.classList.add('border-red-400', 'bg-red-50');
                        break;
                    case 'critical':
                        div.classList.add('border-red-600', 'bg-red-100');
                        break;
                }
                div.classList.remove('border-gray-200');
            } else {
                div.classList.add('border-gray-200');
                div.classList.remove('border-green-400', 'bg-green-50', 'border-yellow-400', 'bg-yellow-50', 'border-red-400', 'bg-red-50', 'border-red-600', 'bg-red-100');
            }
        });
    }

    updateSpecificTypes(reportType) {
        const specificTypeSelect = document.getElementById('specificType');
        specificTypeSelect.innerHTML = '<option value="">Select issue type</option>';

        const options = this.getSpecificTypeOptions(reportType);
        
        options.forEach(option => {
            const optionElement = document.createElement('option');
            optionElement.value = option.value;
            optionElement.textContent = option.label;
            specificTypeSelect.appendChild(optionElement);
        });
    }

    getSpecificTypeOptions(reportType) {
        const options = {
            health: [
                { value: 'respiratory', label: 'Respiratory Issues (Cough, Breathing)' },
                { value: 'allergic', label: 'Allergic Reactions' },
                { value: 'skin', label: 'Skin Irritation/Rash' },
                { value: 'eye_irritation', label: 'Eye Irritation' },
                { value: 'nausea', label: 'Nausea/Digestive Issues' },
                { value: 'headache', label: 'Headaches/Dizziness' },
                { value: 'illness_outbreak', label: 'Illness Outbreak' },
                { value: 'other_health', label: 'Other Health Symptom' }
            ],
            environmental: [
                { value: 'air_pollution', label: 'Air Quality/Pollution' },
                { value: 'water_contamination', label: 'Water Contamination' },
                { value: 'chemical_spill', label: 'Chemical Spill/Hazardous Materials' },
                { value: 'noise_pollution', label: 'Excessive Noise' },
                { value: 'odor', label: 'Strong/Unusual Odors' },
                { value: 'waste_disposal', label: 'Improper Waste Disposal' },
                { value: 'industrial_emissions', label: 'Industrial Emissions' },
                { value: 'other_environmental', label: 'Other Environmental Issue' }
            ],
            weather: [
                { value: 'severe_storm', label: 'Severe Thunderstorm' },
                { value: 'flooding', label: 'Flooding' },
                { value: 'extreme_heat', label: 'Extreme Heat' },
                { value: 'extreme_cold', label: 'Extreme Cold' },
                { value: 'high_winds', label: 'High Winds' },
                { value: 'hail', label: 'Hail' },
                { value: 'tornado', label: 'Tornado/Funnel Cloud' },
                { value: 'ice_storm', label: 'Ice Storm' },
                { value: 'other_weather', label: 'Other Weather Event' }
            ],
            emergency: [
                { value: 'fire', label: 'Fire' },
                { value: 'explosion', label: 'Explosion' },
                { value: 'building_collapse', label: 'Building/Structure Damage' },
                { value: 'power_outage', label: 'Extended Power Outage' },
                { value: 'gas_leak', label: 'Gas Leak' },
                { value: 'infrastructure_failure', label: 'Infrastructure Failure' },
                { value: 'mass_casualty', label: 'Mass Casualty Event' },
                { value: 'other_emergency', label: 'Other Emergency' }
            ]
        };

        return options[reportType] || [];
    }

    loadSpecificTypes() {
        // Load default options for health (first option)
        this.updateSpecificTypes('health');
    }

    handleDragOver(e) {
        e.preventDefault();
        e.currentTarget.classList.add('dragover');
    }

    handleDragLeave(e) {
        e.preventDefault();
        e.currentTarget.classList.remove('dragover');
    }

    handleDrop(e) {
        e.preventDefault();
        e.currentTarget.classList.remove('dragover');
        this.handleFileSelect(e.dataTransfer.files);
    }

    handleFileSelect(files) {
        const fileArray = Array.from(files);
        
        fileArray.forEach(file => {
            if (this.uploadedPhotos.length >= this.maxPhotos) {
                this.showToast('Maximum 3 photos allowed', 'warning');
                return;
            }

            if (!file.type.startsWith('image/')) {
                this.showToast('Please select image files only', 'error');
                return;
            }

            if (file.size > 5 * 1024 * 1024) {
                this.showToast('File size must be less than 5MB', 'error');
                return;
            }

            this.addPhoto(file);
        });
    }

    addPhoto(file) {
        const reader = new FileReader();
        
        reader.onload = (e) => {
            const photoData = {
                file: file,
                url: e.target.result,
                id: Date.now() + Math.random()
            };

            this.uploadedPhotos.push(photoData);
            this.updatePhotoPreview();
        };

        reader.readAsDataURL(file);
    }

    updatePhotoPreview() {
        const previewContainer = document.getElementById('photoPreview');
        
        if (this.uploadedPhotos.length === 0) {
            previewContainer.classList.add('hidden');
            return;
        }

        previewContainer.classList.remove('hidden');
        previewContainer.innerHTML = '';

        this.uploadedPhotos.forEach((photo, index) => {
            const photoDiv = document.createElement('div');
            photoDiv.className = 'image-preview';
            photoDiv.innerHTML = `
                <img src="${photo.url}" alt="Preview ${index + 1}">
                <button type="button" class="remove-image" onclick="reportForm.removePhoto(${photo.id})">
                    <i class="fas fa-times"></i>
                </button>
            `;
            previewContainer.appendChild(photoDiv);
        });

        // Animate new photos
        anime({
            targets: '.image-preview',
            scale: [0.8, 1],
            opacity: [0, 1],
            duration: 300,
            easing: 'easeOutCubic'
        });
    }

    removePhoto(photoId) {
        this.uploadedPhotos = this.uploadedPhotos.filter(photo => photo.id !== photoId);
        this.updatePhotoPreview();
    }

    toggleContactFields(isAnonymous) {
        const contactFields = document.querySelectorAll('input[name="contactName"], input[name="contactEmail"], input[name="contactPhone"]');
        
        contactFields.forEach(field => {
            if (isAnonymous) {
                field.disabled = true;
                field.value = '';
                field.style.opacity = '0.5';
            } else {
                field.disabled = false;
                field.style.opacity = '1';
            }
        });
    }

    async autoFillLocation(e) {
        const zipCode = e.target.value;
        if (zipCode.length === 5) {
            try {
                // This would typically call a geocoding service
                // For now, we'll just show a placeholder
                console.log('Auto-filling location for ZIP:', zipCode);
            } catch (error) {
                console.error('Error auto-filling location:', error);
            }
        }
    }

    async handleSubmit(e) {
        e.preventDefault();
        
        const submitButton = e.target.querySelector('button[type="submit"]');
        const spinner = submitButton.querySelector('.animate-spin');
        
        // Show loading state
        submitButton.disabled = true;
        spinner.classList.remove('hidden');

        try {
            const formData = new FormData(e.target);
            
            // Add photos to form data
            this.uploadedPhotos.forEach((photo, index) => {
                formData.append(`photo_${index}`, photo.file);
            });

            // Add timestamp
            formData.append('timestamp', new Date().toISOString());
            formData.append('photos_count', this.uploadedPhotos.length);

            const response = await fetch('/api/submit-report', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                this.showSuccessModal();
                this.resetForm();
            } else {
                throw new Error('Failed to submit report');
            }
        } catch (error) {
            console.error('Error submitting report:', error);
            this.showToast('Failed to submit report. Please try again.', 'error');
        } finally {
            // Hide loading state
            submitButton.disabled = false;
            spinner.classList.add('hidden');
        }
    }

    showSuccessModal() {
        const modal = document.getElementById('successModal');
        modal.classList.remove('hidden');
        
        // Animate modal
        anime({
            targets: modal.querySelector('div'),
            scale: [0.8, 1],
            opacity: [0, 1],
            duration: 400,
            easing: 'easeOutCubic'
        });
    }

    closeSuccessModal() {
        const modal = document.getElementById('successModal');
        modal.classList.add('hidden');
    }

    resetForm() {
        document.getElementById('reportForm').reset();
        this.uploadedPhotos = [];
        this.updatePhotoPreview();
        
        // Reset visual selections
        document.querySelectorAll('.report-type-option div, .severity-option div').forEach(div => {
            div.className = 'border-2 border-gray-200 rounded-lg p-4 transition-all hover:border-blue-400 hover:bg-blue-50';
        });
        
        // Reset contact fields
        this.toggleContactFields(false);
    }

    showToast(message, type = 'info') {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg max-w-sm ${
            type === 'error' ? 'bg-red-500 text-white' :
            type === 'warning' ? 'bg-yellow-500 text-black' :
            type === 'success' ? 'bg-green-500 text-white' :
            'bg-blue-500 text-white'
        }`;
        toast.innerHTML = `
            <div class="flex items-center justify-between">
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-xl">&times;</button>
            </div>
        `;
        
        document.body.appendChild(toast);
        
        // Animate in
        anime({
            targets: toast,
            translateX: [300, 0],
            opacity: [0, 1],
            duration: 300,
            easing: 'easeOutCubic'
        });
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (document.body.contains(toast)) {
                anime({
                    targets: toast,
                    translateX: [0, 300],
                    opacity: [1, 0],
                    duration: 300,
                    easing: 'easeInCubic',
                    complete: () => toast.remove()
                });
            }
        }, 5000);
    }
}

// Initialize the report form when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.reportForm = new ReportForm();
});