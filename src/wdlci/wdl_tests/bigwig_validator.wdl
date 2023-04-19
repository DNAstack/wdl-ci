version 1.0

# Validate input bigWig files
# Input type: bigWig file

task bigwig_validator {
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

		validate_bw() {
			test_file=$1

			python3.9 -c "import pyBigWig; bw = pyBigWig.open('$test_file'); bw.isBigWig();"
		}

		# Confirm that validated output is bigwig-format
		if ! (validate_bw ~{validated_output}); then
			err "Validated output file [~{basename(validated_output)}] is not a valid bigWig file"
			exit 1
		fi

		# Confirm that current output is bigwig-format
		if (validate_bw ~{current_run_output}); then
			echo "Current run output [~{basename(current_run_output)}] is a valid bigWig file"
		else
			err "Current run output [~{basename(current_run_output)}] is not a valid bigWig file"
			exit 1
		fi
	>>>

	output {
	}

	runtime {
		docker: "dnastack/dnastack-wdl-ci-tools:0.0.1"
		cpu: 1
		memory: "3.75 GB"
		disk: disk_size + " GB"
		disks: "local-disk " + disk_size + " HDD"
		preemptible: 1
	}
}
