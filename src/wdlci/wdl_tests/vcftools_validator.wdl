version 1.0

# VCFtools validator on input files
# Input type: file.vcf.gz

task vcftools_validator {
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

		if ! vcf-validator ~{validated_output}; then
			err "Validated VCF: [~{basename(validated_output)}] is invalid"
			exit 1
		else
			if ! vcf-validator ~{current_run_output}; then
				err "Current VCF: [~{basename(current_run_output)}] is invalid"
				exit 1
			else
				echo "Current VCF: [~{basename(current_run_output)}] passed VCFtools validator"
			fi
		fi
	>>>

	output {
		#Int rc = read_int("rc")
	}

	runtime {
		docker: "biocontainers/vcftools:v0.1.16-1-deb_cv1"
		cpu: 1
		memory: "3.75 GB"
		disk: disk_size + " GB"
		disks: "local-disk " + disk_size + " HDD"
		preemptible: 1
	}
}
