%% Hyperspectral Image Processing for Agriculture Monitoring
% This script processes hyperspectral images for crop health analysis
% using MATLAB's Hyperspectral Imaging Library and Image Processing Toolbox

function results = hyperspectral_processor(image_path, output_path)
    %% Input Parameters
    % image_path: Path to the hyperspectral image file
    % output_path: Path to save processed results
    
    try
        %% Load Hyperspectral Image
        fprintf('Loading hyperspectral image: %s\n', image_path);
        
        % Check if file exists
        if ~exist(image_path, 'file')
            error('Image file not found: %s', image_path);
        end
        
        % Load hyperspectral data
        % Note: This assumes ENVI format - adjust for your specific format
        hcube = hypercube(image_path);
        
        % Display basic information
        fprintf('Image dimensions: %dx%dx%d (Height x Width x Bands)\n', ...
            size(hcube.DataCube, 1), size(hcube.DataCube, 2), size(hcube.DataCube, 3));
        fprintf('Wavelength range: %.2f - %.2f nm\n', ...
            min(hcube.Wavelength), max(hcube.Wavelength));
        
        %% Band Calibration and Preprocessing
        fprintf('Performing band calibration and preprocessing...\n');
        
        % Apply atmospheric correction if needed
        % corrected_hcube = atmosphericCorrection(hcube);
        
        % Noise reduction using smoothing
        smoothed_cube = smoothdata(hcube.DataCube, 3, 'movmean', 3);
        
        % Normalize spectral data
        normalized_cube = normalize_spectral_data(smoothed_cube);
        
        %% Feature Extraction - Vegetation Indices
        fprintf('Calculating vegetation indices...\n');
        
        % Calculate NDVI (Normalized Difference Vegetation Index)
        ndvi_map = calculate_ndvi(hcube);
        
        % Calculate SAVI (Soil-Adjusted Vegetation Index)
        savi_map = calculate_savi(hcube);
        
        % Calculate EVI (Enhanced Vegetation Index)
        evi_map = calculate_evi(hcube);
        
        % Calculate MCARI (Modified Chlorophyll Absorption Ratio Index)
        mcari_map = calculate_mcari(hcube);
        
        % Calculate Red Edge Position
        rep_map = calculate_red_edge_position(hcube);
        
        %% Soil Health Analysis
        fprintf('Analyzing soil conditions...\n');
        
        % Calculate soil brightness index
        soil_brightness = calculate_soil_brightness(hcube);
        
        % Estimate soil moisture content
        soil_moisture = estimate_soil_moisture(hcube);
        
        %% Statistical Analysis
        fprintf('Performing statistical analysis...\n');
        
        % Calculate statistics for each index
        ndvi_stats = calculate_image_statistics(ndvi_map);
        savi_stats = calculate_image_statistics(savi_map);
        evi_stats = calculate_image_statistics(evi_map);
        
        %% Generate Output Maps
        fprintf('Generating output maps...\n');
        
        % Create output directory if it doesn't exist
        if ~exist(output_path, 'dir')
            mkdir(output_path);
        end
        
        % Save index maps as GeoTIFF
        save_index_map(ndvi_map, fullfile(output_path, 'ndvi_map.tif'));
        save_index_map(savi_map, fullfile(output_path, 'savi_map.tif'));
        save_index_map(evi_map, fullfile(output_path, 'evi_map.tif'));
        save_index_map(mcari_map, fullfile(output_path, 'mcari_map.tif'));
        save_index_map(rep_map, fullfile(output_path, 'red_edge_map.tif'));
        
        % Generate false color composites
        generate_false_color_composite(hcube, fullfile(output_path, 'false_color.png'));
        
        % Generate visualization plots
        create_visualization_plots(ndvi_map, savi_map, evi_map, output_path);
        
        %% Compile Results
        results = struct();
        results.processing_status = 'success';
        results.timestamp = datetime('now');
        results.input_file = image_path;
        results.output_path = output_path;
        results.image_dimensions = size(hcube.DataCube);
        results.wavelength_range = [min(hcube.Wavelength), max(hcube.Wavelength)];
        results.ndvi_stats = ndvi_stats;
        results.savi_stats = savi_stats;
        results.evi_stats = evi_stats;
        results.soil_brightness_mean = mean(soil_brightness(:), 'omitnan');
        results.soil_moisture_mean = mean(soil_moisture(:), 'omitnan');
        
        % Save results to JSON
        results_json = jsonencode(results);
        fid = fopen(fullfile(output_path, 'processing_results.json'), 'w');
        fprintf(fid, '%s', results_json);
        fclose(fid);
        
        fprintf('Processing completed successfully!\n');
        
    catch ME
        fprintf('Error during processing: %s\n', ME.message);
        results = struct();
        results.processing_status = 'error';
        results.error_message = ME.message;
        results.timestamp = datetime('now');
    end
end

%% Helper Functions

function normalized_cube = normalize_spectral_data(data_cube)
    % Normalize spectral data to [0, 1] range
    normalized_cube = zeros(size(data_cube));
    for i = 1:size(data_cube, 3)
        band = data_cube(:, :, i);
        min_val = min(band(:));
        max_val = max(band(:));
        if max_val > min_val
            normalized_cube(:, :, i) = (band - min_val) / (max_val - min_val);
        else
            normalized_cube(:, :, i) = band;
        end
    end
end

function ndvi = calculate_ndvi(hcube)
    % Calculate NDVI using red and near-infrared bands
    red_band = find_closest_wavelength(hcube.Wavelength, 670);  % Red ~670nm
    nir_band = find_closest_wavelength(hcube.Wavelength, 800);  % NIR ~800nm
    
    red = double(hcube.DataCube(:, :, red_band));
    nir = double(hcube.DataCube(:, :, nir_band));
    
    ndvi = (nir - red) ./ (nir + red + eps);
    ndvi(ndvi < -1) = -1;
    ndvi(ndvi > 1) = 1;
end

function savi = calculate_savi(hcube)
    % Calculate SAVI with soil adjustment factor L=0.5
    red_band = find_closest_wavelength(hcube.Wavelength, 670);
    nir_band = find_closest_wavelength(hcube.Wavelength, 800);
    
    red = double(hcube.DataCube(:, :, red_band));
    nir = double(hcube.DataCube(:, :, nir_band));
    
    L = 0.5;  % Soil adjustment factor
    savi = ((nir - red) ./ (nir + red + L)) * (1 + L);
end

function evi = calculate_evi(hcube)
    % Calculate EVI using blue, red, and NIR bands
    blue_band = find_closest_wavelength(hcube.Wavelength, 470);  % Blue ~470nm
    red_band = find_closest_wavelength(hcube.Wavelength, 670);   % Red ~670nm
    nir_band = find_closest_wavelength(hcube.Wavelength, 800);   % NIR ~800nm
    
    blue = double(hcube.DataCube(:, :, blue_band));
    red = double(hcube.DataCube(:, :, red_band));
    nir = double(hcube.DataCube(:, :, nir_band));
    
    % EVI coefficients
    G = 2.5;
    C1 = 6;
    C2 = 7.5;
    L = 1;
    
    evi = G * ((nir - red) ./ (nir + C1 * red - C2 * blue + L));
end

function mcari = calculate_mcari(hcube)
    % Calculate MCARI for chlorophyll content estimation
    green_band = find_closest_wavelength(hcube.Wavelength, 550);  % Green ~550nm
    red_band = find_closest_wavelength(hcube.Wavelength, 670);    % Red ~670nm
    red_edge_band = find_closest_wavelength(hcube.Wavelength, 700); % Red edge ~700nm
    
    green = double(hcube.DataCube(:, :, green_band));
    red = double(hcube.DataCube(:, :, red_band));
    red_edge = double(hcube.DataCube(:, :, red_edge_band));
    
    mcari = ((red_edge - red) - 0.2 * (red_edge - green)) .* (red_edge ./ red);
end

function rep = calculate_red_edge_position(hcube)
    % Calculate Red Edge Position for stress detection
    wavelengths = hcube.Wavelength;
    red_edge_start = find_closest_wavelength(wavelengths, 680);
    red_edge_end = find_closest_wavelength(wavelengths, 750);
    
    [rows, cols, ~] = size(hcube.DataCube);
    rep = zeros(rows, cols);
    
    for i = 1:rows
        for j = 1:cols
            spectrum = squeeze(hcube.DataCube(i, j, red_edge_start:red_edge_end));
            [~, max_idx] = max(gradient(spectrum));
            rep(i, j) = wavelengths(red_edge_start + max_idx - 1);
        end
    end
end

function brightness = calculate_soil_brightness(hcube)
    % Calculate soil brightness index
    visible_bands = hcube.Wavelength >= 400 & hcube.Wavelength <= 700;
    visible_data = hcube.DataCube(:, :, visible_bands);
    brightness = mean(visible_data, 3);
end

function moisture = estimate_soil_moisture(hcube)
    % Estimate soil moisture using water absorption bands
    water_band1 = find_closest_wavelength(hcube.Wavelength, 1450);  % Water absorption ~1450nm
    water_band2 = find_closest_wavelength(hcube.Wavelength, 1950);  % Water absorption ~1950nm
    ref_band = find_closest_wavelength(hcube.Wavelength, 1650);     % Reference band ~1650nm
    
    if water_band1 > 0 && water_band2 > 0 && ref_band > 0
        water1 = double(hcube.DataCube(:, :, water_band1));
        water2 = double(hcube.DataCube(:, :, water_band2));
        ref = double(hcube.DataCube(:, :, ref_band));
        
        moisture = (ref - (water1 + water2) / 2) ./ (ref + (water1 + water2) / 2);
    else
        moisture = zeros(size(hcube.DataCube, 1), size(hcube.DataCube, 2));
    end
end

function band_idx = find_closest_wavelength(wavelengths, target)
    % Find the band index closest to target wavelength
    [~, band_idx] = min(abs(wavelengths - target));
end

function stats = calculate_image_statistics(image_data)
    % Calculate basic statistics for an image
    valid_data = image_data(~isnan(image_data) & ~isinf(image_data));
    
    stats = struct();
    stats.mean = mean(valid_data);
    stats.median = median(valid_data);
    stats.std = std(valid_data);
    stats.min = min(valid_data);
    stats.max = max(valid_data);
    stats.percentile_25 = prctile(valid_data, 25);
    stats.percentile_75 = prctile(valid_data, 75);
end

function save_index_map(index_map, filepath)
    % Save index map as GeoTIFF
    try
        geotiffwrite(filepath, index_map);
    catch
        % If GeoTIFF writing fails, save as regular TIFF
        imwrite(mat2gray(index_map), filepath);
    end
end

function generate_false_color_composite(hcube, filepath)
    % Generate false color composite (NIR-Red-Green)
    nir_band = find_closest_wavelength(hcube.Wavelength, 800);
    red_band = find_closest_wavelength(hcube.Wavelength, 670);
    green_band = find_closest_wavelength(hcube.Wavelength, 550);
    
    nir = mat2gray(hcube.DataCube(:, :, nir_band));
    red = mat2gray(hcube.DataCube(:, :, red_band));
    green = mat2gray(hcube.DataCube(:, :, green_band));
    
    false_color = cat(3, nir, red, green);
    imwrite(false_color, filepath);
end

function create_visualization_plots(ndvi, savi, evi, output_path)
    % Create visualization plots for vegetation indices
    figure('Position', [100, 100, 1200, 400]);
    
    subplot(1, 3, 1);
    imagesc(ndvi, [-1, 1]);
    colorbar;
    title('NDVI');
    colormap(gca, parula);
    
    subplot(1, 3, 2);
    imagesc(savi, [0, 2]);
    colorbar;
    title('SAVI');
    colormap(gca, parula);
    
    subplot(1, 3, 3);
    imagesc(evi, [0, 1]);
    colorbar;
    title('EVI');
    colormap(gca, parula);
    
    saveas(gcf, fullfile(output_path, 'vegetation_indices.png'));
    close(gcf);
end
