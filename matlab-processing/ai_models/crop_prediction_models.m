%% AI Models for Crop Health and Pest Prediction
% This script implements CNN and LSTM models using MATLAB's Deep Learning Toolbox
% for spectral classification and forecasting stress/pest outbreaks

classdef crop_prediction_models < handle
    
    properties (Access = private)
        cnn_model
        lstm_model
        scaler_params
        class_labels
        is_trained = false
    end
    
    methods
        function obj = crop_prediction_models()
            % Constructor
            fprintf('Initializing Crop Prediction Models...\n');
            obj.class_labels = {'healthy', 'stress', 'disease', 'pest'};
        end
        
        function train_cnn_classifier(obj, spectral_data, labels, validation_split)
            % Train CNN for spectral classification
            % Input:
            %   spectral_data: [N x bands] spectral signatures
            %   labels: [N x 1] categorical labels
            %   validation_split: fraction for validation (default: 0.2)
            
            if nargin < 4
                validation_split = 0.2;
            end
            
            fprintf('Training CNN classifier...\n');
            
            try
                % Prepare data
                [X_train, X_val, y_train, y_val] = obj.split_data(spectral_data, labels, validation_split);
                
                % Reshape for CNN input (add spatial dimensions)
                [num_samples, num_bands] = size(X_train);
                X_train_cnn = reshape(X_train', [1, num_bands, 1, num_samples]);
                X_val_cnn = reshape(X_val', [1, num_bands, 1, size(X_val, 1)]);
                
                % Define CNN architecture
                layers = [
                    imageInputLayer([1 num_bands 1], 'Name', 'input', 'Normalization', 'none')
                    
                    % First convolutional block
                    convolution2dLayer([1 16], 32, 'Padding', 'same', 'Name', 'conv1')
                    batchNormalizationLayer('Name', 'bn1')
                    reluLayer('Name', 'relu1')
                    dropoutLayer(0.2, 'Name', 'dropout1')
                    
                    % Second convolutional block
                    convolution2dLayer([1 8], 64, 'Padding', 'same', 'Name', 'conv2')
                    batchNormalizationLayer('Name', 'bn2')
                    reluLayer('Name', 'relu2')
                    maxPooling2dLayer([1 2], 'Name', 'pool1')
                    dropoutLayer(0.3, 'Name', 'dropout2')
                    
                    % Third convolutional block
                    convolution2dLayer([1 4], 128, 'Padding', 'same', 'Name', 'conv3')
                    batchNormalizationLayer('Name', 'bn3')
                    reluLayer('Name', 'relu3')
                    averagePooling2dLayer([1 2], 'Name', 'pool2')
                    dropoutLayer(0.4, 'Name', 'dropout3')
                    
                    % Dense layers
                    fullyConnectedLayer(256, 'Name', 'fc1')
                    reluLayer('Name', 'relu4')
                    dropoutLayer(0.5, 'Name', 'dropout4')
                    
                    fullyConnectedLayer(128, 'Name', 'fc2')
                    reluLayer('Name', 'relu5')
                    dropoutLayer(0.3, 'Name', 'dropout5')
                    
                    % Output layer
                    fullyConnectedLayer(length(obj.class_labels), 'Name', 'fc_out')
                    softmaxLayer('Name', 'softmax')
                    classificationLayer('Name', 'output')
                ];
                
                % Training options
                options = trainingOptions('adam', ...
                    'InitialLearnRate', 0.001, ...
                    'MaxEpochs', 100, ...
                    'MiniBatchSize', 32, ...
                    'ValidationData', {X_val_cnn, y_val}, ...
                    'ValidationFrequency', 10, ...
                    'ValidationPatience', 10, ...
                    'Shuffle', 'every-epoch', ...
                    'Plots', 'training-progress', ...
                    'Verbose', false);
                
                % Train the network
                obj.cnn_model = trainNetwork(X_train_cnn, y_train, layers, options);
                
                % Evaluate model
                y_pred = classify(obj.cnn_model, X_val_cnn);
                accuracy = sum(y_pred == y_val) / numel(y_val);
                fprintf('CNN Validation Accuracy: %.2f%%\n', accuracy * 100);
                
                % Generate confusion matrix
                figure('Position', [100, 100, 600, 500]);
                confusionchart(y_val, y_pred);
                title('CNN Classification Results');
                
                obj.is_trained = true;
                fprintf('CNN training completed successfully!\n');
                
            catch ME
                fprintf('Error during CNN training: %s\n', ME.message);
                rethrow(ME);
            end
        end
        
        function train_lstm_forecaster(obj, time_series_data, targets, sequence_length)
            % Train LSTM for time series forecasting
            % Input:
            %   time_series_data: [N x features x time] sensor time series
            %   targets: [N x 1] future stress/pest outbreak indicators
            %   sequence_length: number of time steps for LSTM input
            
            if nargin < 4
                sequence_length = 24; % Default: 24 time steps
            end
            
            fprintf('Training LSTM forecaster...\n');
            
            try
                % Prepare sequences
                [X_seq, y_seq] = obj.prepare_sequences(time_series_data, targets, sequence_length);
                
                % Split data
                [X_train, X_val, y_train, y_val] = obj.split_data(X_seq, y_seq, 0.2);
                
                % Reshape for LSTM (features x sequence_length x samples)
                X_train_lstm = permute(X_train, [2, 3, 1]);
                X_val_lstm = permute(X_val, [2, 3, 1]);
                
                % Define LSTM architecture
                num_features = size(X_train_lstm, 1);
                
                layers = [
                    sequenceInputLayer(num_features, 'Name', 'input')
                    
                    % First LSTM layer
                    lstmLayer(128, 'OutputMode', 'sequence', 'Name', 'lstm1')
                    dropoutLayer(0.3, 'Name', 'dropout1')
                    
                    % Second LSTM layer
                    lstmLayer(64, 'OutputMode', 'last', 'Name', 'lstm2')
                    dropoutLayer(0.4, 'Name', 'dropout2')
                    
                    % Dense layers
                    fullyConnectedLayer(32, 'Name', 'fc1')
                    reluLayer('Name', 'relu1')
                    dropoutLayer(0.3, 'Name', 'dropout3')
                    
                    fullyConnectedLayer(16, 'Name', 'fc2')
                    reluLayer('Name', 'relu2')
                    
                    % Output layer (regression for risk score)\n                    fullyConnectedLayer(1, 'Name', 'output')
                    regressionLayer('Name', 'regression')
                ];
                
                % Training options
                options = trainingOptions('adam', ...
                    'InitialLearnRate', 0.01, ...
                    'LearnRateSchedule', 'piecewise', ...
                    'LearnRateDropFactor', 0.1, ...
                    'LearnRateDropPeriod', 20, ...
                    'MaxEpochs', 80, ...
                    'MiniBatchSize', 64, ...
                    'ValidationData', {X_val_lstm, y_val}, ...
                    'ValidationFrequency', 10, ...
                    'ValidationPatience', 8, ...
                    'Shuffle', 'every-epoch', ...
                    'Plots', 'training-progress', ...
                    'Verbose', false);
                
                % Train the network
                obj.lstm_model = trainNetwork(X_train_lstm, y_train, layers, options);
                
                % Evaluate model
                y_pred = predict(obj.lstm_model, X_val_lstm);
                rmse = sqrt(mean((y_pred - y_val).^2));
                r2 = 1 - sum((y_val - y_pred).^2) / sum((y_val - mean(y_val)).^2);
                
                fprintf('LSTM Validation RMSE: %.4f\n', rmse);
                fprintf('LSTM Validation R²: %.4f\n', r2);
                
                % Plot predictions vs actual
                figure('Position', [100, 100, 800, 400]);
                subplot(1, 2, 1);
                scatter(y_val, y_pred, 50, 'filled', 'Alpha', 0.6);
                xlabel('Actual Risk Score');
                ylabel('Predicted Risk Score');
                title('LSTM Predictions vs Actual');
                hold on;
                plot([min(y_val), max(y_val)], [min(y_val), max(y_val)], 'r--', 'LineWidth', 2);
                hold off;
                
                subplot(1, 2, 2);
                residuals = y_val - y_pred;
                histogram(residuals, 20);
                xlabel('Residuals');
                ylabel('Frequency');
                title('Prediction Residuals');
                
                obj.is_trained = true;
                fprintf('LSTM training completed successfully!\n');
                
            catch ME
                fprintf('Error during LSTM training: %s\n', ME.message);
                rethrow(ME);
            end
        end
        
        function predictions = predict_crop_health(obj, spectral_data)
            % Predict crop health from spectral data using trained CNN
            
            if ~obj.is_trained || isempty(obj.cnn_model)
                error('CNN model not trained. Please train the model first.');
            end
            
            % Reshape input for CNN
            [num_samples, num_bands] = size(spectral_data);
            X_cnn = reshape(spectral_data', [1, num_bands, 1, num_samples]);
            
            % Make predictions
            [pred_labels, pred_scores] = classify(obj.cnn_model, X_cnn);
            
            % Format output
            predictions = struct();
            predictions.labels = pred_labels;
            predictions.probabilities = pred_scores;
            predictions.confidence = max(pred_scores, [], 2);
            
            % Add interpretation
            for i = 1:length(pred_labels)
                switch char(pred_labels(i))
                    case 'healthy'
                        predictions.recommendation{i} = 'Crop is healthy. Continue normal monitoring.';
                    case 'stress'
                        predictions.recommendation{i} = 'Crop shows signs of stress. Check irrigation and nutrients.';
                    case 'disease'
                        predictions.recommendation{i} = 'Disease detected. Consider fungicide treatment.';
                    case 'pest'
                        predictions.recommendation{i} = 'Pest activity detected. Apply appropriate pesticide.';
                end
            end
        end
        
        function forecast = forecast_risk(obj, sensor_data, forecast_horizon)
            % Forecast future risk using trained LSTM
            
            if ~obj.is_trained || isempty(obj.lstm_model)
                error('LSTM model not trained. Please train the model first.');
            end
            
            if nargin < 3
                forecast_horizon = 7; % Default: 7 days ahead
            end
            
            % Prepare input sequence
            sequence_length = size(sensor_data, 3);
            X_lstm = permute(sensor_data, [2, 3, 1]); % features x time x samples
            
            % Make forecast
            risk_scores = predict(obj.lstm_model, X_lstm);
            
            % Generate multi-step forecast if needed
            if forecast_horizon > 1
                forecasted_risks = zeros(size(risk_scores, 1), forecast_horizon);
                forecasted_risks(:, 1) = risk_scores;
                
                % Iterative forecasting (simplified approach)
                current_sequence = sensor_data;
                for h = 2:forecast_horizon
                    % Update sequence with predicted values
                    % This is a simplified approach - in practice, you'd use
                    % more sophisticated methods
                    next_risk = predict(obj.lstm_model, permute(current_sequence, [2, 3, 1]));
                    forecasted_risks(:, h) = next_risk;
                    
                    % Shift sequence and add predicted value
                    current_sequence = circshift(current_sequence, -1, 3);
                    % In practice, you'd update with actual next sensor readings
                end
            else
                forecasted_risks = risk_scores;
            end
            
            % Format output
            forecast = struct();
            forecast.risk_scores = forecasted_risks;
            forecast.horizon_days = forecast_horizon;
            forecast.risk_level = obj.categorize_risk(forecasted_risks);
            forecast.recommendations = obj.generate_recommendations(forecasted_risks);
        end
        
        function save_models(obj, filepath)
            % Save trained models
            if obj.is_trained
                model_data = struct();
                model_data.cnn_model = obj.cnn_model;
                model_data.lstm_model = obj.lstm_model;
                model_data.scaler_params = obj.scaler_params;
                model_data.class_labels = obj.class_labels;
                model_data.timestamp = datetime('now');
                
                save(filepath, 'model_data');
                fprintf('Models saved to: %s\n', filepath);
            else
                warning('No trained models to save.');
            end
        end
        
        function load_models(obj, filepath)
            % Load pre-trained models
            if exist(filepath, 'file')
                data = load(filepath);
                obj.cnn_model = data.model_data.cnn_model;
                obj.lstm_model = data.model_data.lstm_model;
                obj.scaler_params = data.model_data.scaler_params;
                obj.class_labels = data.model_data.class_labels;
                obj.is_trained = true;
                
                fprintf('Models loaded from: %s\n', filepath);
            else
                error('Model file not found: %s', filepath);
            end
        end
    end
    
    methods (Access = private)
        function [X_train, X_val, y_train, y_val] = split_data(obj, X, y, validation_split)
            % Split data into training and validation sets
            n_samples = size(X, 1);
            n_val = round(n_samples * validation_split);
            
            % Random split
            indices = randperm(n_samples);
            val_indices = indices(1:n_val);
            train_indices = indices(n_val+1:end);
            
            X_train = X(train_indices, :, :);
            X_val = X(val_indices, :, :);
            y_train = y(train_indices);
            y_val = y(val_indices);
        end
        
        function [X_seq, y_seq] = prepare_sequences(obj, time_series_data, targets, sequence_length)
            % Prepare sequences for LSTM training
            [n_samples, n_features, n_timesteps] = size(time_series_data);
            
            if n_timesteps < sequence_length
                error('Time series too short for specified sequence length');
            end
            
            n_sequences = n_timesteps - sequence_length + 1;
            X_seq = zeros(n_samples * n_sequences, n_features, sequence_length);
            y_seq = zeros(n_samples * n_sequences, 1);
            
            idx = 1;
            for i = 1:n_samples
                for j = 1:n_sequences
                    X_seq(idx, :, :) = time_series_data(i, :, j:j+sequence_length-1);
                    y_seq(idx) = targets(i);
                    idx = idx + 1;
                end
            end
        end
        
        function risk_categories = categorize_risk(obj, risk_scores)
            % Categorize continuous risk scores into discrete levels
            risk_categories = cell(size(risk_scores));
            
            for i = 1:numel(risk_scores)
                score = risk_scores(i);
                if score < 0.3
                    risk_categories{i} = 'Low';
                elseif score < 0.6
                    risk_categories{i} = 'Medium';
                elseif score < 0.8
                    risk_categories{i} = 'High';
                else
                    risk_categories{i} = 'Critical';
                end
            end
        end
        
        function recommendations = generate_recommendations(obj, risk_scores)
            % Generate actionable recommendations based on risk scores
            recommendations = cell(size(risk_scores));
            
            for i = 1:numel(risk_scores)
                score = risk_scores(i);
                if score < 0.3
                    recommendations{i} = 'Continue regular monitoring and maintenance.';
                elseif score < 0.6
                    recommendations{i} = 'Increase monitoring frequency. Check for early stress indicators.';
                elseif score < 0.8
                    recommendations{i} = 'Take preventive action. Consider irrigation adjustments or pest control measures.';
                else
                    recommendations{i} = 'Immediate intervention required. Apply treatments and increase surveillance.';
                end
            end
        end
    end
end
