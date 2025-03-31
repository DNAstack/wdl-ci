version 1.0

# Validate input RDS files
# Input type: RDS file

task check_rds {
	input {
		File current_run_output
		File validated_output
	}

	Int disk_size = ceil(size(current_run_output, "GB") + size(validated_output, "GB") + 10)

	command <<<
		set -euo pipefail

		err() {
			message=$1

			echo -e "[ERROR] $message" >&2
		}

		validate_rds() {
			test_file=$1

			Rscript -e "tryCatch({obj <- readRDS('$test_file', refhook = NULL)}, error = function(e) { message('Error: ', e$message); quit(status = 1) })"
		}

		# Confirm that validated output is RDS format
		if ! (validate_rds ~{validated_output}); then
			err "Validated output file [~{basename(validated_output)}] is not a valid RDS file"
			exit 1
		fi

		# Confirm that current output is RDS format
		if (validate_rds ~{current_run_output}); then
			echo "Current run output [~{basename(current_run_output)}] is a valid RDS file"
		else
			err "Current run output [~{basename(current_run_output)}] is not a valid RDS file"
			exit 1
		fi
	>>>

	output {
	}

	runtime {
		docker: "dnastack/dnastack-wdl-ci-tools:0.1.0"
		cpu: 1
		memory: "3.75 GB"
		disk: disk_size + " GB"
		disks: "local-disk " + disk_size + " HDD"
		preemptible: 1
	}
}
