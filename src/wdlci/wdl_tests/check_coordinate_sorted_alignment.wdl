version 1.0

# Check if input files are sorted by coordinates
# Input type: SAM/BAM/CRAM

task check_coordinate_sorted_alignment {
	input {
		File current_run_output
		File validated_output
	}

	Int disk_size = ceil(size(current_run_output, "GB") + size(validated_output, "GB") + 50)

	command <<<
		set -euo pipefail

		err() {
			message=$1

			echo -e "[ERROR] $message" >&2
		}

		# Using samtools view -H and @HD-SO sort order header tag
		if ! samtools view -H ~{validated_output} | grep "SO:coordinate"; then
			err "Validated output: [~{basename(validated_output)}] is not sorted by coordinate"
			exit 1
		else
			if ! samtools view -H ~{current_run_output} | grep "SO:coordinate"; then
				err "Current run output: [~{basename(current_run_output)}] is not sorted by coordinate"
				exit 1
			else
				echo "Current run output: [~{basename(current_run_output)}] is sorted by coordinate"
			fi
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
