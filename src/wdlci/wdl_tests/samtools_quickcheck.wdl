version 1.0

# Samtools quickcheck on input files
# Input type: SAM/BAM/CRAM

task samtools_quickcheck {
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

		if ! samtools quickcheck ~{validated_output}; then
			err "Validated BAM file did not pass samtools quickcheck"
			exit 1
		else
			if ! samtools quickcheck ~{current_run_output}; then
				err "Current BAM file did not pass samtools quickcheck"
				exit 1
			else
				echo "BAM file passed samtools quickcheck"
			fi
		fi
	>>>

	output {
		#Int rc = read_int("rc")
	}

	runtime {
		docker: "biocontainers/samtools:v1.9-4-deb_cv1"
		cpu: 1
		memory: "3.75 GB"
		disk: disk_size + " GB"
		disks: "local-disk " + disk_size + " HDD"
		preemptible: 1
	}
}
