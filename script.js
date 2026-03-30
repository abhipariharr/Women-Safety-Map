// Pune Women's Safety Map - Main Script
// Author: Claude Code
// Version: 2.0 (with Flask API support)

// ============================================
// Configuration
// ============================================

// API Mode: Set to true when running with Flask backend
// Set to false for static file mode (direct HTML open)
const USE_API = false;
const API_BASE = 'http://localhost:5000';

// Pune center coordinates
const PUNE_CENTER = [18.5204, 73.8567];
const DEFAULT_ZOOM = 12;

// ============================================
// Global Variables
// ============================================

let map;
let heatLayer;
let crimeMarkers = [];
let allCrimeData = [];
let filteredData = [];

// ============================================
// Initialization
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    initializeMap();
    loadCrimeData();
    setupEventListeners();
});

// ============================================
// Map Initialization
// ============================================

function initializeMap() {
    // Create Leaflet map centered on Pune
    map = L.map('map').setView(PUNE_CENTER, DEFAULT_ZOOM);

    // Add OpenStreetMap tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 18
    }).addTo(map);

    // Initialize heat layer (will be populated later)
    heatLayer = L.heatLayer([], {
        radius: 25,
        blur: 15,
        maxZoom: 17,
        gradient: {
            0.0: '#00ff00',   // Green - safer
            0.5: '#ffff00',   // Yellow - moderate
            0.8: '#ff6600',   // Orange
            1.0: '#ff0000'    // Red - highly unsafe
        }
    }).addTo(map);
}

// ============================================
// Data Loading
// ============================================

async function loadCrimeData() {
    try {
        let url = USE_API ? `${API_BASE}/api/crimes` : 'data.json';

        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();

        // Handle API response format
        allCrimeData = USE_API ? result.data : result;
        filteredData = [...allCrimeData];

        // Process and display data
        processData();
        updateStats();
        updateHeatmap();

        console.log(`Loaded ${allCrimeData.length} crime records (API: ${USE_API})`);
    } catch (error) {
        console.error('Error loading crime data:', error);

        // Fallback: try loading local file if API fails
        if (USE_API) {
            console.log('Falling back to local data.json...');
            try {
                const response = await fetch('data.json');
                allCrimeData = await response.json();
                filteredData = [...allCrimeData];
                processData();
                updateStats();
                updateHeatmap();
                console.log(`Fallback: Loaded ${allCrimeData.length} records`);
            } catch (fallbackError) {
                alert('Error loading crime data. Please ensure data.json exists or Flask is running.');
            }
        } else {
            alert('Error loading crime data. Please ensure data.json exists.');
        }
    }
}

// ============================================
// Data Processing
// ============================================

function processData() {
    // Clear existing markers
    clearMarkers();

    // Aggregate crimes by area for markers
    const aggregatedCrimes = aggregateByArea(filteredData);

    // Create markers for each area
    Object.values(aggregatedCrimes).forEach(areaData => {
        createCrimeMarker(areaData);
    });

    // Fit map to show all markers
    if (crimeMarkers.length > 0) {
        const group = new L.featureGroup(crimeMarkers);
        map.fitBounds(group.getBounds().pad(0.1));
    }
}

function aggregateByArea(data) {
    const aggregated = {};

    data.forEach(record => {
        const key = record.area;

        if (!aggregated[key]) {
            aggregated[key] = {
                area: record.area,
                latitude: record.latitude,
                longitude: record.longitude,
                crimes: [],
                totalCount: 0
            };
        }

        aggregated[key].crimes.push({
            type: record.crime_type,
            count: record.crime_count,
            year: record.year
        });

        aggregated[key].totalCount += record.crime_count;
    });

    return aggregated;
}

// ============================================
// Marker Creation
// ============================================

function createCrimeMarker(areaData) {
    // Determine risk level based on total crime count
    const riskLevel = getRiskLevel(areaData.totalCount);
    const color = getRiskColor(riskLevel);

    // Create circle marker
    const marker = L.circleMarker([areaData.latitude, areaData.longitude], {
        radius: Math.min(Math.max(areaData.totalCount / 10, 8), 25),
        fillColor: color,
        color: '#333',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.7
    }).addTo(map);

    // Build popup content
    const popupContent = buildPopupContent(areaData);
    marker.bindPopup(popupContent);

    // Add to markers array
    crimeMarkers.push(marker);
}

function buildPopupContent(areaData) {
    const crimeBreakdown = areaData.crimes.map(c =>
        `<li><strong>${formatCrimeType(c.type)}:</strong> ${c.count} incidents</li>`
    ).join('');

    const riskLevel = getRiskLevel(areaData.totalCount);
    const riskLabel = riskLevel === 'high' ? 'HIGH RISK' :
                      riskLevel === 'medium' ? 'MODERATE' : 'LOW RISK';
    const riskColor = riskLevel === 'high' ? 'text-danger' :
                      riskLevel === 'medium' ? 'text-warning' : 'text-success';

    return `
        <div class="crime-popup">
            <h6 class="mb-2">${areaData.area}</h6>
            <p class="mb-1 ${riskColor}"><strong>${riskLabel}</strong></p>
            <p class="mb-1"><strong>Total:</strong> ${areaData.totalCount} incidents</p>
            <hr class="my-2">
            <p class="mb-1"><strong>Crime Breakdown:</strong></p>
            <ul class="mb-0 small">${crimeBreakdown}</ul>
        </div>
    `;
}

function formatCrimeType(type) {
    const types = {
        'harassment': 'Harassment',
        'assault': 'Assault',
        'stalking': 'Stalking',
        'domestic_violence': 'Domestic Violence',
        'dowry_deaths': 'Dowry Deaths',
        'other': 'Other Crimes'
    };
    return types[type] || type;
}

// ============================================
// Risk Assessment
// ============================================

function getRiskLevel(totalCrimes) {
    if (totalCrimes >= 80) return 'high';
    if (totalCrimes >= 40) return 'medium';
    return 'low';
}

function getRiskColor(riskLevel) {
    switch (riskLevel) {
        case 'high': return '#ff0000';
        case 'medium': return '#ffff00';
        case 'low': return '#00ff00';
        default: return '#ffff00';
    }
}

// ============================================
// Heatmap Update
// ============================================

function updateHeatmap() {
    const heatPoints = [];

    // Aggregate crime counts by location for heatmap
    const locationCrime = {};

    filteredData.forEach(record => {
        const key = `${record.latitude},${record.longitude}`;

        if (!locationCrime[key]) {
            locationCrime[key] = {
                lat: record.latitude,
                lng: record.longitude,
                intensity: 0
            };
        }

        locationCrime[key].intensity += record.crime_count;
    });

    // Convert to heat layer format [lat, lng, intensity]
    Object.values(locationCrime).forEach(loc => {
        // Normalize intensity (scale 0-1)
        const normalizedIntensity = Math.min(loc.intensity / 150, 1.0);
        heatPoints.push([loc.lat, loc.lng, normalizedIntensity]);
    });

    // Update heat layer
    heatLayer.setLatLngs(heatPoints);
}

// ============================================
// Statistics Update
// ============================================

function updateStats() {
    // Total crimes
    const totalCrimes = filteredData.reduce((sum, record) => sum + record.crime_count, 0);
    document.getElementById('totalCrimes').textContent = totalCrimes;

    // Total unique areas
    const uniqueAreas = new Set(filteredData.map(r => r.area));
    document.getElementById('totalAreas').textContent = uniqueAreas.size;

    // Highest risk area
    const areaTotals = {};
    filteredData.forEach(record => {
        areaTotals[record.area] = (areaTotals[record.area] || 0) + record.crime_count;
    });

    const highestRiskArea = Object.entries(areaTotals)
        .sort((a, b) => b[1] - a[1])[0];
    document.getElementById('highestRisk').textContent =
        highestRiskArea ? highestRiskArea[0] : '-';

    // Most common crime type
    const crimeTypeTotals = {};
    filteredData.forEach(record => {
        crimeTypeTotals[record.crime_type] =
            (crimeTypeTotals[record.crime_type] || 0) + record.crime_count;
    });

    const mostCommon = Object.entries(crimeTypeTotals)
        .sort((a, b) => b[1] - a[1])[0];
    document.getElementById('mostCommon').textContent =
        mostCommon ? formatCrimeType(mostCommon[0]) : '-';
}

// ============================================
// Event Listeners
// ============================================

function setupEventListeners() {
    // Crime type filter checkboxes
    const filterCheckboxes = document.querySelectorAll('.crime-filter');
    filterCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', handleFilterChange);
    });

    // Search input
    const searchInput = document.getElementById('searchInput');
    searchInput.addEventListener('input', handleSearch);
    searchInput.addEventListener('keyup', handleSearchKeyup);
}

// ============================================
// Filter Handling
// ============================================

function handleFilterChange(event) {
    const checkbox = event.target;
    const value = checkbox.value;

    // If "All" is checked, uncheck others and show all
    if (value === 'all' && checkbox.checked) {
        document.querySelectorAll('.crime-filter:not(#filterAll)').forEach(cb => {
            cb.checked = false;
        });
    }

    // If any other checkbox is checked, uncheck "All"
    if (value !== 'all' && checkbox.checked) {
        document.getElementById('filterAll').checked = false;
    }

    // If all individual checkboxes are unchecked, check "All"
    const anyChecked = Array.from(document.querySelectorAll('.crime-filter:not(#filterAll)'))
        .some(cb => cb.checked);

    if (!anyChecked) {
        document.getElementById('filterAll').checked = true;
    }

    applyFilters();
}

function applyFilters() {
    const selectedTypes = getSelectedCrimeTypes();

    if (selectedTypes.includes('all')) {
        filteredData = [...allCrimeData];
    } else {
        filteredData = allCrimeData.filter(record =>
            selectedTypes.includes(record.crime_type)
        );
    }

    processData();
    updateStats();
    updateHeatmap();
}

function getSelectedCrimeTypes() {
    const types = [];

    if (document.getElementById('filterAll').checked) {
        types.push('all');
    } else {
        document.querySelectorAll('.crime-filter:checked').forEach(cb => {
            if (cb.value !== 'all') {
                types.push(cb.value);
            }
        });
    }

    return types;
}

// ============================================
// Search Handling
// ============================================

function handleSearch(event) {
    const query = event.target.value.toLowerCase().trim();
    const resultsContainer = document.getElementById('searchResults');

    if (query.length < 2) {
        resultsContainer.innerHTML = '';
        return;
    }

    // Use API for search if enabled
    if (USE_API) {
        fetch(`${API_BASE}/api/search?q=${encodeURIComponent(query)}`)
            .then(res => res.json())
            .then(result => {
                displaySearchResults(result.data);
            })
            .catch(err => {
                console.error('Search error:', err);
                // Fallback to local search
                localSearch(query);
            });
    } else {
        localSearch(query);
    }
}

function localSearch(query) {
    const uniqueAreas = [...new Set(allCrimeData.map(r => r.area))];
    const matches = uniqueAreas.filter(area =>
        area.toLowerCase().includes(query)
    );
    displaySearchResults(matches);
}

function displaySearchResults(matches) {
    const resultsContainer = document.getElementById('searchResults');
    if (matches.length > 0) {
        resultsContainer.innerHTML = matches.slice(0, 5).map(area =>
            `<div class="search-result p-2 border-bottom" style="cursor:pointer"
                  onclick="focusOnArea('${area}')">${area}</div>`
        ).join('');
    } else {
        resultsContainer.innerHTML = '<div class="text-muted p-2">No areas found</div>';
    }
}

function handleSearchKeyup(event) {
    if (event.key === 'Enter') {
        const query = event.target.value.toLowerCase().trim();
        if (query.length > 0) {
            const uniqueAreas = [...new Set(allCrimeData.map(r => r.area))];
            const match = uniqueAreas.find(area =>
                area.toLowerCase() === query
            );

            if (match) {
                focusOnArea(match);
            }
        }
    }
}

function focusOnArea(areaName) {
    // Find the area's coordinates
    const areaRecord = allCrimeData.find(r => r.area === areaName);

    if (areaRecord) {
        // Pan to the area
        map.setView([areaRecord.latitude, areaRecord.longitude], 15);

        // Find and open the marker popup
        crimeMarkers.forEach(marker => {
            if (marker.getLatLng().lat === areaRecord.latitude &&
                marker.getLatLng().lng === areaRecord.longitude) {
                marker.openPopup();
            }
        });
    }

    // Clear search
    document.getElementById('searchInput').value = areaName;
    document.getElementById('searchResults').innerHTML = '';
}

function clearSearchHighlights() {
    crimeMarkers.forEach(marker => {
        // Reset marker style if needed
    });
}

// ============================================
// Utility Functions
// ============================================

function clearMarkers() {
    crimeMarkers.forEach(marker => {
        map.removeLayer(marker);
    });
    crimeMarkers = [];
}

// ============================================
// Debug (remove in production)
// ============================================

function logData() {
    console.log('All Data:', allCrimeData);
    console.log('Filtered Data:', filteredData);
}
