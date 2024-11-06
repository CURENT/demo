clc;
clear;

cases = { 'case14.m'; 'case39.m'; 'case89pegase.m'; 'case118.m';
    'npcc.m'; 'wecc.m'; 'case300.m'; 'pglib_opf_case1354_pegase.m';
    'pglib_opf_case2869_pegase.m'; 'pglib_opf_case4020_goc.m';
    'pglib_opf_case5658_epigrids.m'; 'pglib_opf_case7336_epigrids.m' };

function [time, obj] = mptest(case_file)
    % Load the case
    mpc = loadcase(case_file);
    
    % relax line flow limits, otherwise DCOPF faild
    if size(mpc.bus, 1) > 4000
        mpc.branch(:, 6) = 999;   % RATE_A
    end

    % config
    mpopt = mpoption('VERBOSE', 0, 'OUT_ALL', 0, ...
                'OPF_ALG_DC', 250, 'OPF_ALG', 560, ...
                'OPF_IGNORE_ANG_LIM', false, ...
                'OPF_FLOW_LIM', 0);
    t_matpower = tic;
    mpc_sol = rundcopf(mpc, mpopt);
    s_matpower = toc(t_matpower);
    
    time = s_matpower * 1000;  % scale to ms
    obj = mpc_sol.f;
end

cols_time = {'matpower'}; cols_obj = {'matpower'};

n_iters = 10;
time_data = zeros(n_iters, length(cases), length(cols_time));
obj_data = zeros(length(cases), length(cols_obj));

for n_case = 1:length(cases)
    case_file = cases{n_case};
    disp(['Case: ', case_file]);
    for n_iter = 1:n_iters
        [time, obj] = mptest(case_file);
        time_data(n_iter, n_case, :) = time;
    end
    obj_data(n_case, :) = obj;
end

% Optionally, re-enable warnings if needed elsewhere in your code warning('on', 'all');

% Calculate mean times 
mean_times = mean(time_data, 1);

% Prepare CSV output
csv_output = "Case,Obj,TimeMean";
for i = 1:n_iters
    csv_output = csv_output + ",Time" + i;
end
csv_output = csv_output + newline;

for n_case = 1:length(cases)
    case_file = cases{n_case};
    case_name = strrep(case_file, '.m', '');
    csv_output = csv_output + case_name + "," + num2str(obj_data(n_case, 1)) + "," + num2str(mean_times(1, n_case, 1));
    for n_iter = 1:n_iters
        csv_output = csv_output + "," + num2str(time_data(n_iter, n_case, 1));
    end
    csv_output = csv_output + newline;
end

% Write the CSV output to a file
fileID = fopen('results_matpower.csv', 'w');
fprintf(fileID, '%s', csv_output);
fclose(fileID);