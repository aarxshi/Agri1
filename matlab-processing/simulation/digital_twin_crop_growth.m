%% Digital Twin Simulation for Crop Growth
% This script creates and runs a Simulink-based digital twin simulation
% for crop growth modeling and scenario testing

classdef digital_twin_crop_growth < handle
    
    properties (Access = private)
        model_name = 'CropGrowthDigitalTwin'
        simulation_results
        crop_parameters
        weather_data
        soil_parameters
        is_initialized = false
    end
    
    methods
        function obj = digital_twin_crop_growth()
            % Constructor
            fprintf('Initializing Digital Twin Crop Growth Simulation...\n');
            obj.initialize_default_parameters();
        end
        
        function create_simulink_model(obj)
            % Create Simulink model for crop growth simulation
            
            fprintf('Creating Simulink digital twin model...\n');
            
            try
                % Create new Simulink model
                new_system(obj.model_name);
                open_system(obj.model_name);
                
                % Add main subsystems
                obj.add_weather_subsystem();
                obj.add_soil_subsystem();
                obj.add_plant_growth_subsystem();
                obj.add_stress_detection_subsystem();
                obj.add_irrigation_controller();
                obj.add_data_logging();
                
                % Connect subsystems
                obj.connect_model_blocks();
                
                % Configure simulation parameters
                set_param(obj.model_name, 'SolverType', 'Variable-step');
                set_param(obj.model_name, 'Solver', 'ode45');
                set_param(obj.model_name, 'StartTime', '0');
                set_param(obj.model_name, 'StopTime', '365'); % One year simulation
                set_param(obj.model_name, 'MaxStep', '1'); % Daily time step
                
                % Save model
                save_system(obj.model_name);
                
                obj.is_initialized = true;
                fprintf('Simulink model created successfully: %s.slx\n', obj.model_name);
                
            catch ME
                fprintf('Error creating Simulink model: %s\n', ME.message);
                rethrow(ME);
            end
        end
        
        function run_simulation(obj, duration_days, scenarios)
            % Run digital twin simulation with different scenarios
            % Input:
            %   duration_days: Simulation duration in days
            %   scenarios: Structure with different scenario parameters
            
            if ~obj.is_initialized
                obj.create_simulink_model();
            end
            
            fprintf('Running digital twin simulation for %d days...\n', duration_days);
            
            try
                % Set simulation stop time
                set_param(obj.model_name, 'StopTime', num2str(duration_days));
                
                % Initialize results storage
                obj.simulation_results = struct();
                
                if nargin < 3 || isempty(scenarios)
                    scenarios = obj.create_default_scenarios();
                end
                
                % Run simulation for each scenario
                scenario_names = fieldnames(scenarios);
                for i = 1:length(scenario_names)
                    scenario_name = scenario_names{i};
                    scenario = scenarios.(scenario_name);
                    
                    fprintf('Running scenario: %s\n', scenario_name);
                    
                    % Apply scenario parameters
                    obj.apply_scenario_parameters(scenario);
                    
                    % Run simulation
                    sim_out = sim(obj.model_name);
                    
                    % Store results
                    obj.simulation_results.(scenario_name) = obj.extract_simulation_data(sim_out);
                    
                    % Generate scenario report
                    obj.generate_scenario_report(scenario_name, obj.simulation_results.(scenario_name));
                end
                
                % Compare scenarios
                obj.compare_scenarios();
                
                fprintf('Digital twin simulation completed successfully!\n');
                
            catch ME
                fprintf('Error during simulation: %s\n', ME.message);
                rethrow(ME);
            end
        end
        
        function optimize_irrigation(obj, target_yield, water_constraints)
            % Optimize irrigation schedule using simulation
            % Input:
            %   target_yield: Desired crop yield (kg/ha)
            %   water_constraints: Maximum water usage (mm/day)
            
            fprintf('Optimizing irrigation schedule...\n');
            
            if ~obj.is_initialized
                obj.create_simulink_model();
            end
            
            try
                % Define optimization parameters
                irrigation_variables = [0.1:0.1:2.0]; % mm/day range
                irrigation_frequency = [1:7]; % days between irrigation
                
                best_yield = 0;
                best_water_use = inf;
                optimal_schedule = [];
                
                % Grid search for optimal irrigation parameters
                for water_rate = irrigation_variables
                    for frequency = irrigation_frequency
                        if water_rate * (365/frequency) <= water_constraints * 365
                            % Test this irrigation strategy
                            yield_result = obj.test_irrigation_strategy(water_rate, frequency);
                            
                            if yield_result >= target_yield && ...
                               water_rate * (365/frequency) < best_water_use
                                best_yield = yield_result;
                                best_water_use = water_rate * (365/frequency);
                                optimal_schedule = [water_rate, frequency];
                            end
                        end
                    end
                end
                
                % Generate optimization results
                optimization_results = struct();
                optimization_results.target_yield = target_yield;
                optimization_results.achieved_yield = best_yield;
                optimization_results.water_constraint = water_constraints * 365;
                optimization_results.optimal_water_use = best_water_use;
                optimization_results.optimal_irrigation_rate = optimal_schedule(1);
                optimization_results.optimal_frequency = optimal_schedule(2);
                optimization_results.efficiency = best_yield / best_water_use; % kg/mm
                
                % Save optimization results
                obj.save_optimization_results(optimization_results);
                
                fprintf('Irrigation optimization completed!\n');
                fprintf('Optimal irrigation rate: %.1f mm every %d days\n', ...
                    optimal_schedule(1), optimal_schedule(2));
                fprintf('Expected yield: %.1f kg/ha\n', best_yield);
                fprintf('Total water use: %.1f mm/year\n', best_water_use);
                
                return optimization_results;
                
            catch ME
                fprintf('Error during irrigation optimization: %s\n', ME.message);
                rethrow(ME);
            end
        end
        
        function results = predict_climate_impact(obj, climate_scenarios)
            % Predict crop performance under different climate scenarios
            % Input:
            %   climate_scenarios: Structure with temperature, rainfall, CO2 changes
            
            fprintf('Predicting climate change impacts...\n');
            
            if ~obj.is_initialized
                obj.create_simulink_model();
            end
            
            try
                results = struct();
                
                % Baseline scenario (current climate)
                baseline_result = obj.run_baseline_simulation();
                results.baseline = baseline_result;
                
                % Climate change scenarios
                scenario_names = fieldnames(climate_scenarios);
                for i = 1:length(scenario_names)
                    scenario_name = scenario_names{i};
                    scenario = climate_scenarios.(scenario_name);
                    
                    fprintf('Testing climate scenario: %s\n', scenario_name);
                    
                    % Modify climate parameters
                    modified_weather = obj.apply_climate_changes(obj.weather_data, scenario);
                    
                    % Run simulation with modified climate
                    scenario_result = obj.run_climate_simulation(modified_weather);
                    results.(scenario_name) = scenario_result;
                    
                    % Calculate impact metrics
                    results.(scenario_name).yield_change_percent = ...
                        ((scenario_result.final_yield - baseline_result.final_yield) / ...
                         baseline_result.final_yield) * 100;
                    
                    results.(scenario_name).water_stress_increase = ...
                        scenario_result.avg_water_stress - baseline_result.avg_water_stress;
                end
                
                % Generate climate impact report
                obj.generate_climate_report(results);
                
                fprintf('Climate impact analysis completed!\n');
                
            catch ME
                fprintf('Error during climate impact prediction: %s\n', ME.message);
                rethrow(ME);
            end
        end
        
        function save_results(obj, filepath)
            % Save simulation results
            if ~isempty(obj.simulation_results)
                save(filepath, 'simulation_results', '-struct', 'obj.simulation_results');
                fprintf('Simulation results saved to: %s\n', filepath);
            else
                warning('No simulation results to save.');
            end
        end
    end
    
    methods (Access = private)
        function initialize_default_parameters(obj)
            % Initialize default crop, soil, and weather parameters
            
            % Crop parameters (generic crop model)
            obj.crop_parameters = struct();
            obj.crop_parameters.max_yield = 8000; % kg/ha
            obj.crop_parameters.growth_rate = 0.1; % 1/day
            obj.crop_parameters.water_requirement = 500; % mm/season
            obj.crop_parameters.temperature_optimum = 25; % °C
            obj.crop_parameters.temperature_min = 10; % °C
            obj.crop_parameters.temperature_max = 35; % °C
            obj.crop_parameters.photoperiod_sensitivity = 0.1;
            obj.crop_parameters.harvest_index = 0.45;
            
            % Soil parameters
            obj.soil_parameters = struct();
            obj.soil_parameters.field_capacity = 300; % mm
            obj.soil_parameters.wilting_point = 100; % mm
            obj.soil_parameters.saturation = 450; % mm
            obj.soil_parameters.infiltration_rate = 50; % mm/day
            obj.soil_parameters.evaporation_rate = 3; % mm/day
            obj.soil_parameters.organic_matter = 0.03; % fraction
            
            % Generate synthetic weather data
            obj.weather_data = obj.generate_weather_data(365);
        end
        
        function weather = generate_weather_data(obj, days)
            % Generate synthetic weather data for simulation
            
            % Create daily weather data
            weather = struct();
            weather.day = (1:days)';
            weather.doy = mod(weather.day - 1, 365) + 1; % Day of year
            
            % Temperature (sinusoidal with noise)
            temp_mean = 20;
            temp_amplitude = 10;
            temp_noise = 3;
            weather.temperature = temp_mean + temp_amplitude * sin(2*pi*weather.doy/365) + ...
                                  temp_noise * randn(days, 1);
            
            % Solar radiation (correlated with temperature)
            solar_mean = 20; % MJ/m²/day
            solar_amplitude = 10;
            weather.solar_radiation = solar_mean + solar_amplitude * sin(2*pi*weather.doy/365) + ...
                                     2 * randn(days, 1);
            weather.solar_radiation(weather.solar_radiation < 0) = 0;
            
            % Rainfall (stochastic)
            rainfall_probability = 0.3;
            rainfall_amounts = exprnd(10, days, 1); % Exponential distribution
            weather.rainfall = rainfall_amounts .* (rand(days, 1) < rainfall_probability);
            
            % Relative humidity
            weather.humidity = 60 + 20 * sin(2*pi*weather.doy/365) + 10 * randn(days, 1);
            weather.humidity = max(30, min(95, weather.humidity)); % Constrain to realistic range
            
            % Wind speed
            weather.wind_speed = 2 + 1 * randn(days, 1);
            weather.wind_speed(weather.wind_speed < 0) = 0;
        end
        
        function add_weather_subsystem(obj)
            % Add weather data subsystem to Simulink model
            
            % Create weather subsystem
            add_block('simulink/Ports & Subsystems/Subsystem', ...
                [obj.model_name '/Weather_System']);
            
            % Add weather data blocks (simplified representation)
            % In practice, this would include detailed weather input blocks
            add_block('simulink/Sources/From Workspace', ...
                [obj.model_name '/Weather_System/Temperature']);
            add_block('simulink/Sources/From Workspace', ...
                [obj.model_name '/Weather_System/Solar_Radiation']);
            add_block('simulink/Sources/From Workspace', ...
                [obj.model_name '/Weather_System/Rainfall']);
            
            % Add output ports
            add_block('simulink/Ports & Subsystems/Out1', ...
                [obj.model_name '/Weather_System/Temp_Out']);
            add_block('simulink/Ports & Subsystems/Out1', ...
                [obj.model_name '/Weather_System/Solar_Out']);
            add_block('simulink/Ports & Subsystems/Out1', ...
                [obj.model_name '/Weather_System/Rain_Out']);
        end
        
        function add_soil_subsystem(obj)
            % Add soil water balance subsystem
            
            add_block('simulink/Ports & Subsystems/Subsystem', ...
                [obj.model_name '/Soil_System']);
            
            % Add soil water balance components
            add_block('simulink/Continuous/Integrator', ...
                [obj.model_name '/Soil_System/Soil_Water_Content']);
            add_block('simulink/Math Operations/Add', ...
                [obj.model_name '/Soil_System/Water_Balance']);
            
            % Add output port
            add_block('simulink/Ports & Subsystems/Out1', ...
                [obj.model_name '/Soil_System/Soil_Moisture_Out']);
        end
        
        function add_plant_growth_subsystem(obj)
            % Add plant growth dynamics subsystem
            
            add_block('simulink/Ports & Subsystems/Subsystem', ...
                [obj.model_name '/Plant_Growth']);
            
            % Add growth rate calculation
            add_block('simulink/Math Operations/Product', ...
                [obj.model_name '/Plant_Growth/Growth_Rate_Calc']);
            add_block('simulink/Continuous/Integrator', ...
                [obj.model_name '/Plant_Growth/Biomass_Accumulation']);
            
            % Add output port
            add_block('simulink/Ports & Subsystems/Out1', ...
                [obj.model_name '/Plant_Growth/Biomass_Out']);
        end
        
        function add_stress_detection_subsystem(obj)
            % Add stress detection and quantification
            
            add_block('simulink/Ports & Subsystems/Subsystem', ...
                [obj.model_name '/Stress_Detection']);
            
            % Add stress indicators
            add_block('simulink/Logic and Bit Operations/Logical Operator', ...
                [obj.model_name '/Stress_Detection/Water_Stress']);
            add_block('simulink/Logic and Bit Operations/Logical Operator', ...
                [obj.model_name '/Stress_Detection/Heat_Stress']);
            
            % Add output port
            add_block('simulink/Ports & Subsystems/Out1', ...
                [obj.model_name '/Stress_Detection/Stress_Level_Out']);
        end
        
        function add_irrigation_controller(obj)
            % Add intelligent irrigation controller
            
            add_block('simulink/Ports & Subsystems/Subsystem', ...
                [obj.model_name '/Irrigation_Controller']);
            
            % Add control logic
            add_block('simulink/Logic and Bit Operations/Compare To Constant', ...
                [obj.model_name '/Irrigation_Controller/Moisture_Threshold']);
            add_block('simulink/Discontinuities/Switch', ...
                [obj.model_name '/Irrigation_Controller/Irrigation_Switch']);
            
            % Add output port
            add_block('simulink/Ports & Subsystems/Out1', ...
                [obj.model_name '/Irrigation_Controller/Irrigation_Out']);
        end
        
        function add_data_logging(obj)
            % Add data logging blocks
            
            add_block('simulink/Sinks/To Workspace', ...
                [obj.model_name '/Log_Biomass']);
            add_block('simulink/Sinks/To Workspace', ...
                [obj.model_name '/Log_Soil_Moisture']);
            add_block('simulink/Sinks/To Workspace', ...
                [obj.model_name '/Log_Stress_Level']);
            
            % Configure logging parameters
            set_param([obj.model_name '/Log_Biomass'], 'VariableName', 'biomass_data');
            set_param([obj.model_name '/Log_Soil_Moisture'], 'VariableName', 'soil_moisture_data');
            set_param([obj.model_name '/Log_Stress_Level'], 'VariableName', 'stress_data');
        end
        
        function connect_model_blocks(obj)
            % Connect all subsystem blocks
            % This is a simplified representation - actual connections would be more complex
            
            fprintf('Connecting model blocks...\n');
            % In practice, you would add specific connection lines here
            % add_line(obj.model_name, 'Weather_System/1', 'Plant_Growth/1');
            % etc.
        end
        
        function scenarios = create_default_scenarios(obj)
            % Create default simulation scenarios
            
            scenarios = struct();
            
            % Optimal conditions scenario
            scenarios.optimal = struct();
            scenarios.optimal.irrigation_rate = 1.0; % mm/day
            scenarios.optimal.fertilizer_level = 1.0; % relative to baseline
            scenarios.optimal.temperature_adjustment = 0; % °C
            
            % Drought scenario
            scenarios.drought = struct();
            scenarios.drought.irrigation_rate = 0.5; % mm/day
            scenarios.drought.fertilizer_level = 1.0;
            scenarios.drought.temperature_adjustment = 2; % °C increase
            scenarios.drought.rainfall_reduction = 0.5; % 50% reduction
            
            % High temperature scenario
            scenarios.heat_stress = struct();
            scenarios.heat_stress.irrigation_rate = 1.0;
            scenarios.heat_stress.fertilizer_level = 1.0;
            scenarios.heat_stress.temperature_adjustment = 5; % °C increase
        end
        
        function apply_scenario_parameters(obj, scenario)
            % Apply scenario parameters to model
            % This would modify model parameters or input data
            fprintf('Applying scenario parameters...\n');
            
            % Example parameter modifications
            if isfield(scenario, 'temperature_adjustment')
                obj.weather_data.temperature = obj.weather_data.temperature + ...
                    scenario.temperature_adjustment;
            end
            
            if isfield(scenario, 'rainfall_reduction')
                obj.weather_data.rainfall = obj.weather_data.rainfall * ...
                    (1 - scenario.rainfall_reduction);
            end
        end
        
        function data = extract_simulation_data(obj, sim_out)
            % Extract relevant data from simulation output
            
            data = struct();
            
            % Extract logged data (simplified)
            if evalin('base', 'exist(''biomass_data'', ''var'')')
                data.biomass = evalin('base', 'biomass_data');
                data.final_yield = data.biomass.Data(end) * obj.crop_parameters.harvest_index;
            end
            
            if evalin('base', 'exist(''soil_moisture_data'', ''var'')')
                data.soil_moisture = evalin('base', 'soil_moisture_data');
                data.avg_soil_moisture = mean(data.soil_moisture.Data);
            end
            
            if evalin('base', 'exist(''stress_data'', ''var'')')
                data.stress = evalin('base', 'stress_data');
                data.avg_water_stress = mean(data.stress.Data);
                data.stress_days = sum(data.stress.Data > 0.5);
            end
            
            % Calculate additional metrics
            data.water_use_efficiency = data.final_yield / sum(obj.weather_data.rainfall);
            data.simulation_time = datestr(now);
        end
        
        function generate_scenario_report(obj, scenario_name, results)
            % Generate report for individual scenario
            
            fprintf('Generating report for scenario: %s\n', scenario_name);
            
            % Create figure with results
            figure('Position', [100, 100, 1000, 600]);
            
            if isfield(results, 'biomass') && isfield(results, 'soil_moisture')
                subplot(2, 2, 1);
                plot(results.biomass.Time, results.biomass.Data, 'LineWidth', 2);
                title('Biomass Accumulation');
                xlabel('Days');
                ylabel('Biomass (kg/ha)');
                grid on;
                
                subplot(2, 2, 2);
                plot(results.soil_moisture.Time, results.soil_moisture.Data, 'LineWidth', 2);
                title('Soil Moisture');
                xlabel('Days');
                ylabel('Soil Moisture (mm)');
                grid on;
                
                if isfield(results, 'stress')
                    subplot(2, 2, 3);
                    plot(results.stress.Time, results.stress.Data, 'LineWidth', 2, 'Color', 'red');
                    title('Water Stress Level');
                    xlabel('Days');
                    ylabel('Stress Index');
                    grid on;
                end
                
                subplot(2, 2, 4);
                bar_data = [results.final_yield, results.avg_soil_moisture, results.stress_days];
                bar_labels = {'Final Yield', 'Avg Soil Moisture', 'Stress Days'};
                bar(bar_data);
                set(gca, 'XTickLabel', bar_labels);
                title('Summary Metrics');
                grid on;
            end
            
            sgtitle(['Scenario Results: ' scenario_name]);
            
            % Save figure
            saveas(gcf, ['scenario_' scenario_name '_results.png']);
            close(gcf);
        end
        
        function compare_scenarios(obj)
            % Compare all simulated scenarios
            
            fprintf('Comparing simulation scenarios...\n');
            
            scenario_names = fieldnames(obj.simulation_results);
            if length(scenario_names) < 2
                return;
            end
            
            % Extract comparison metrics
            yields = zeros(length(scenario_names), 1);
            water_stress = zeros(length(scenario_names), 1);
            
            for i = 1:length(scenario_names)
                results = obj.simulation_results.(scenario_names{i});
                if isfield(results, 'final_yield')
                    yields(i) = results.final_yield;
                end
                if isfield(results, 'avg_water_stress')
                    water_stress(i) = results.avg_water_stress;
                end
            end
            
            % Create comparison plot
            figure('Position', [100, 100, 800, 600]);
            
            subplot(2, 1, 1);
            bar(yields);
            set(gca, 'XTickLabel', scenario_names);
            title('Yield Comparison Across Scenarios');
            ylabel('Yield (kg/ha)');
            grid on;
            
            subplot(2, 1, 2);
            bar(water_stress, 'FaceColor', 'red');
            set(gca, 'XTickLabel', scenario_names);
            title('Water Stress Comparison');
            ylabel('Average Water Stress');
            grid on;
            
            sgtitle('Scenario Comparison Summary');
            saveas(gcf, 'scenario_comparison.png');
            close(gcf);
        end
        
        function yield = test_irrigation_strategy(obj, water_rate, frequency)
            % Test specific irrigation strategy
            % This is a simplified version - would run actual simulation
            
            % Simplified yield calculation based on water application
            total_water = water_rate * (365 / frequency);
            optimal_water = obj.crop_parameters.water_requirement;
            
            if total_water < optimal_water * 0.5
                yield = obj.crop_parameters.max_yield * 0.3; % Severe water stress
            elseif total_water < optimal_water * 0.8
                yield = obj.crop_parameters.max_yield * 0.7; % Moderate stress
            elseif total_water <= optimal_water * 1.2
                yield = obj.crop_parameters.max_yield; % Optimal
            else
                yield = obj.crop_parameters.max_yield * 0.9; % Over-watering
            end
        end
        
        function save_optimization_results(obj, results)
            % Save irrigation optimization results
            
            % Create optimization report
            filename = 'irrigation_optimization_results.txt';
            fid = fopen(filename, 'w');
            
            fprintf(fid, 'Irrigation Optimization Results\n');
            fprintf(fid, '================================\n\n');
            fprintf(fid, 'Target Yield: %.1f kg/ha\n', results.target_yield);
            fprintf(fid, 'Achieved Yield: %.1f kg/ha\n', results.achieved_yield);
            fprintf(fid, 'Water Constraint: %.1f mm/year\n', results.water_constraint);
            fprintf(fid, 'Optimal Water Use: %.1f mm/year\n', results.optimal_water_use);
            fprintf(fid, 'Optimal Irrigation Rate: %.1f mm per application\n', results.optimal_irrigation_rate);
            fprintf(fid, 'Optimal Frequency: Every %d days\n', results.optimal_frequency);
            fprintf(fid, 'Water Use Efficiency: %.2f kg/mm\n', results.efficiency);
            
            fclose(fid);
            
            fprintf('Optimization results saved to: %s\n', filename);
        end
        
        function baseline = run_baseline_simulation(obj)
            % Run baseline simulation with current climate
            % This is a placeholder - would run actual simulation
            
            baseline = struct();
            baseline.final_yield = obj.crop_parameters.max_yield;
            baseline.avg_water_stress = 0.3;
            baseline.water_use = obj.crop_parameters.water_requirement;
        end
        
        function modified_weather = apply_climate_changes(obj, weather, scenario)
            % Apply climate change scenario to weather data
            
            modified_weather = weather;
            
            if isfield(scenario, 'temperature_change')
                modified_weather.temperature = weather.temperature + scenario.temperature_change;
            end
            
            if isfield(scenario, 'rainfall_change_percent')
                modified_weather.rainfall = weather.rainfall * (1 + scenario.rainfall_change_percent/100);
            end
            
            if isfield(scenario, 'co2_ppm')
                % CO2 fertilization effect (simplified)
                co2_effect = 1 + (scenario.co2_ppm - 400) * 0.0003; % Simple response
                modified_weather.co2_effect = co2_effect;
            end
        end
        
        function result = run_climate_simulation(obj, modified_weather)
            % Run simulation with modified climate data
            % This is a placeholder - would run actual simulation with modified weather
            
            result = struct();
            
            % Simplified climate impact calculation
            temp_stress = max(0, mean(modified_weather.temperature) - 30) * 0.02;
            water_stress = max(0, 1 - sum(modified_weather.rainfall)/500) * 0.5;
            
            co2_benefit = 0;
            if isfield(modified_weather, 'co2_effect')
                co2_benefit = (modified_weather.co2_effect - 1) * 0.3;
            end
            
            yield_factor = 1 - temp_stress - water_stress + co2_benefit;
            
            result.final_yield = obj.crop_parameters.max_yield * max(0.1, yield_factor);
            result.avg_water_stress = min(1, 0.3 + water_stress);
            result.temperature_stress = temp_stress;
        end
        
        function generate_climate_report(obj, results)
            % Generate comprehensive climate impact report
            
            fprintf('Generating climate impact report...\n');
            
            % Create comparison figure
            figure('Position', [100, 100, 1200, 800]);
            
            scenario_names = fieldnames(results);
            yields = zeros(length(scenario_names), 1);
            stress_levels = zeros(length(scenario_names), 1);
            
            for i = 1:length(scenario_names)
                yields(i) = results.(scenario_names{i}).final_yield;
                stress_levels(i) = results.(scenario_names{i}).avg_water_stress;
            end
            
            subplot(2, 2, 1);
            bar(yields);
            set(gca, 'XTickLabel', scenario_names, 'XTickLabelRotation', 45);
            title('Yield Under Different Climate Scenarios');
            ylabel('Yield (kg/ha)');
            grid on;
            
            subplot(2, 2, 2);
            bar(stress_levels, 'FaceColor', 'red');
            set(gca, 'XTickLabel', scenario_names, 'XTickLabelRotation', 45);
            title('Water Stress Levels');
            ylabel('Average Water Stress');
            grid on;
            
            % Calculate yield changes from baseline
            baseline_yield = results.baseline.final_yield;
            yield_changes = ((yields - baseline_yield) / baseline_yield) * 100;
            
            subplot(2, 2, 3);
            bar(yield_changes);
            set(gca, 'XTickLabel', scenario_names, 'XTickLabelRotation', 45);
            title('Yield Change from Baseline (%)');
            ylabel('Yield Change (%)');
            grid on;
            hold on;
            yline(0, '--k', 'LineWidth', 2);
            hold off;
            
            subplot(2, 2, 4);
            scatter(stress_levels, yields, 100, 'filled');
            xlabel('Water Stress Level');
            ylabel('Final Yield (kg/ha)');
            title('Yield vs Water Stress');
            for i = 1:length(scenario_names)
                text(stress_levels(i), yields(i), scenario_names{i}, ...
                     'VerticalAlignment', 'bottom');
            end
            grid on;
            
            sgtitle('Climate Change Impact Analysis');
            saveas(gcf, 'climate_impact_analysis.png');
            close(gcf);
        end
    end
end
