clc;
clear;

warning('off', 'all');

cases = {
    'case5.m';
    'case14.m';
    'case39.m';
    'npcc.m';
    'wecc.m';
};

% Load the CSV file into a table
lfs_data = readtable('lfs_data.csv');
% Convert the table to an array (excluding the header row)
lfs_array = table2array(lfs_data);

cols_time = {'matpower'};
cols_obj = {'matpower'};

n_iters = 10;

time_data = zeros(n_iters, length(cases));
obj_data = zeros(length(cases), length(cols_obj));

for n_iter = 1:n_iters
    for n_case = 1:length(cases)
        case_file = cases{n_case};
        disp(['Case: ', case_file]);
        load_factor = lfs_array(:, n_case);
   
        % Load the case
        mpc = loadcase(case_file);

        % config
        mpopt = mpoption('VERBOSE', 0, 'OUT_ALL', 0, ...
                    'OPF_ALG_DC', 250, 'OPF_ALG', 560, ...
                    'OPF_IGNORE_ANG_LIM', false, ...
                    'OPF_FLOW_LIM', 0);
      
        pd0 = mpc.bus(:, 3);
        obj = 0;
        t_matpower = tic;
        for n_lf = 1:size(load_factor)
            lf = load_factor(n_lf);
            mpc.bus(:, 3) = lf * pd0;
            [mpc_sol, success] = rundcopf(mpc, mpopt);

            if ~success
                break;
            end

            obj = obj + mpc_sol.f;
        end
        s_matpower = toc(t_matpower) * 1000;
        obj_data(n_case, :) = obj;
        time_data(n_iter, n_case) = s_matpower;
    end
end

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
fileID = fopen('./results/results_matpower_repeat.csv', 'w');
fprintf(fileID, '%s', csv_output);
fclose(fileID);

warning('on', 'all');