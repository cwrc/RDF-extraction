#!/usr/bin/perl

use 5.18.2;
use strict;
use warnings;
use utf8;
use XML::LibXML;

my @mapping;
my @category;
my $total = 0;

#
#  Read in the mapping strings and their corresponding CoD instances
#
open(my $ifh1, '<:encoding(UTF-8)', "COD_mapping_strings.txt")
   or die "Could not open file COD_mapping_strings.txt $!";
open(my $ifh2, '<:encoding(UTF-8)', "COD_mapping_categories.txt")
   or die "Could not open file COD_mapping_categories.txt $!";
my $i = 0;
while ( $mapping[$i] = <$ifh1> ) {
   chomp $mapping[$i];
   $category[$i] = <$ifh2>;
   chomp $category[$i];
   $i++;
}
$total = $i - 1;

close($ifh1);
close($ifh2);

#
#  Find the CoD category that is mapped to by the given string
#
sub findCOD {
   my $string = $_[0];
   my $stopflag = 0;
   my $found;
   my $i = 0;

   $i = 0;
   while ( $stopflag == 0 ) {
      if ( $string eq $mapping[$i] ) {
          $found = $category[$i];
          $stopflag = 1;
      } else {
         $i++;
         if ( $i > $total ) {
            $stopflag = 2;
         }
      }
   }
   if ( $stopflag == 1 ) {
      return ( $found );
   } elsif ( $stopflag == 2 ) {
      $stopflag = 0;
      $i = 0;
      while ( $stopflag == 0 ) {
         if ( $string =~ m/$mapping[$i]/ ) {
             $found = $category[$i];
             $stopflag = 1;
         } else {
            $i++;
            if ( $i > $total ) {
               $stopflag = 2;
            }
         }
      }
      return ( $found );
   }
}

#
#  Mainline: does the following functions
#     1) Establishes the mapping from the CAUSE string to Cause of Death instance
#        * Currently only does one Cause of Death - this will be updated in the future
#     2) Prints out separate files for each biography containing:
#        a) All prefix mappings
#        b) Name
#        c) Cause of Death   

#
#  Location of the biography directory with the XML files for each author
#
my $directory = '/Users/debstacey/Research/CWRC/Testing/Output2/biography_output';
my $label;
my $date;
my $deathflag;

my $strPerson    = "";
my $strLabel     = "";
my $strName      = "";
my $strFactor    = "";
my $strSnippet1  = "";
my $strSnippet1a = "";
my $strSnippet1b = "";
my $strSnippet1c = "";
my $strSnippet2  = "";
my $strSnippet2a = "";
my $strSnippet2b = "";
my $strSnippet2c = "";
my $strSnippet2d = "";
my $strSnippet2e = "";
my $strSnippet2f = "";
my $strSnippet2g = "";
my $strSnippet2h = "";
my $cause = "";
my $found = "";
my $name1 = "";

my $count = 0;
my $flag = 0;

opendir (DIR, $directory) or die $!;
while (my $file = readdir(DIR)) {
   $deathflag = 0;
   $label = $file;
   $label =~ s/-b.xml//;
   if ( $file ne "." and $file ne ".." ) {
      $file = $directory."/".$file;

#      my $dom = XML::LibXML->load_xml(location => $file);

       my $dom = XML::LibXML->load_xml(
          location => $file,
          validation => 0,
          load_ext_dtd => 0, # <- That's the key
       );

      my $name = "";
      my $death = "";
      $cause = "";
      my $prose = "";
      my $snippet = "";

#
#  Find the Standard Name of the person in the biography
#
      foreach my $temp ($dom->findnodes('/BIOGRAPHY/DIV0')) {
         $name = $temp->findvalue('./STANDARD');
      }

#
#  Replace comma with underscore and remove blanks
#
      $name1 = "";
      $name1 = $name;
      $name1 =~ s/, /_/;
      $name1 =~ s/,//g;
      $name1 =~ s/ /_/g;
      $name1 =~ s/\.//g;
      $name1 =~ s/'//g;
      $name1 =~ s/\(//g;
      $name1 =~ s/\)//g;
      $strPerson = "data:$name1 a cwrc:NaturalPerson ;\n";
      $strLabel  = "   rdfs:label \"" . $name . "\"^^xsd:string ;\n";
      $strName   = "   foaf:name \"$name\"\^\^xsd:string .\n";

#
#  Find all the causes of death in the Death entry
#
      foreach my $bio ($dom->findnodes('/BIOGRAPHY/DIV0/DIV1/DEATH')) {
         $cause = join '; ', map {
            $_->to_literal();
         } $bio->findnodes('//CAUSE');

#
#  Check if there is a Regularized cause of death
#
         if ( $bio =~ m/CAUSE REG/ ) {
            if ( $bio =~ m/(CAUSE REG="[-\w]+\s*[-\w]+\s*[-\w]+")/ ) {
                $cause = $1;
            }
         }

#
#  Extract the prose/snippet that goes with this cause of death
#
         $prose = $bio->findnodes('./DIV2/CHRONSTRUCT/CHRONPROSE');
         if ( $prose eq "" ) {
            $prose = $bio->findnodes('./CHRONSTRUCT/CHRONPROSE');
         }
         if ( $prose eq "" ) {
            $prose = $bio->findnodes('./DIV2/SHORTPROSE');
         }
         if ( $prose eq "" ) {
            $prose = $bio->findnodes('./SHORTPROSE');
         }
      }

#
#  Extract the Cause of Death snippet from the prose found in the CAUSE
#
      $strSnippet1  = "data:" . $label . "_causeofdeath_context0_Snippet a oa:TextualBody ;\n";
      $strSnippet1a = "   rdfs:label " . "\"" . $name . " DeathContext snippet \" ;\n";
      $strSnippet1b = "   dcterms:description ";
      $count = 0;
      my @words = split / /, $prose;
      foreach my $word ( @words ) {
         $count++;
      }
      if ( $count > 35 ) {
         my $i = 0;
         while ( $i < 35 ) {
            if ( $i > 0 ) {
               $snippet = $snippet . " " . $words[$i++];
            } else {
               $snippet = $words[$i++];
            }
         }
         $strSnippet1b = $strSnippet1b . "\"$snippet\"\^\^xsd:string ;\n";
      } else {
         $strSnippet1b = $strSnippet1b . "\"$prose\"\^\^xsd:string ;\n";
      }
      $strSnippet1c = "   oa:hasSource <http://orlando.cambridge.org/protected/svPeople?formname=r&people_tab=3&person_id=$label#Death> .\n";

      $strSnippet2 = "data:" . $label ."_causeofdeath_context0_describing a cwrc:DeathContext ;\n";
      $strSnippet2a = "   rdfs:label \"" . $name . " DeathContext describing annotation\" ;\n";
      $strSnippet2b = "   dcterms:subject data:$name1 ,\n      ii:";
      $strSnippet2c = "   oa:hasBody [ a oa:TextualBody ;\n";
      $strSnippet2d = "      dcterms:format \"text/turtle\"^^xsd:string ;\n";
      $strSnippet2f = "   oa:hasTarget data:$name1,\n";
      $strSnippet2g = "      data:" . $label . "_causeofdeath_context0_Snippet ;\n";
      $strSnippet2h = "   oa:motivatedBy oa:describing .\n";

#
#  The mapping process: match the cause of death string with a category (either
#  a regularized cause or one extracted from the CAUSE tags
#
#  First check if it is a Regularized Cause of Death (currently 17 have been found in Orlando)
#
      if ( $cause ne "" ) {
         $deathflag = 0;
         if ( $cause =~ /asthma/ ) {
            $strFactor = "   cwrc:hasCauseOfDeath ii:Asthma ; \n";
            $found = "Asthma";
            $deathflag++;
         } elsif ( $cause =~ /cancer/ ) {
            $strFactor = "   cwrc:hasCauseOfDeath ii:Cancer ; \n";
            $found = "Cancer";
            $deathflag++;
         } elsif ( $cause =~ /childbirth/ ) {
            $strFactor = "   cwrc:hasCauseOfDeath ii:Pregnancy_or_childbirth ; \n";
            $found = "Pregnancy_or_childbirth";
            $deathflag++;
         } elsif ( $cause =~ /dementia/ ) {
            $strFactor = "   cwrc:hasCauseOfDeath ii:Alzheimers_disease_dementias ; \n";
            $found = "Alzheimers_disease_dementias";
            $deathflag++;
         } elsif ( $cause =~ /digestive disorder/ ) {
            $strFactor = "   cwrc:hasCauseOfDeath ii:Disease_of_the_digestive_system ; \n";
            $found = "Disease_of_the_digestive_system";
            $deathflag++;
         } elsif ( $cause =~ /drowning/ ) {
            $strFactor = "   cwrc:hasCauseOfDeath ii:Drowning ; \n";
            $found = "Drowning";
            $deathflag++;
         } elsif ( $cause =~ /edema/ ) {
            $strFactor = "   cwrc:hasCauseOfDeath ii:Edema ; \n";
            $found = "Edema";
            $deathflag++;
         } elsif ( $cause =~ /gastro-intestinal disease/ ) {
            $strFactor = "   cwrc:hasCauseOfDeath ii:Disease_of_the_digestive_system ; \n";
            $found = "Disease_of_the_digestive_system";
            $deathflag++;
         } elsif ( $cause =~ /heart failure/ ) {
            $strFactor = "   cwrc:hasCauseOfDeath ii:Disease_of_the_circulatory_system ; \n";
            $found = "Disease_of_the_circulatory_system";
            $deathflag++;
         } elsif ( $cause =~ /kidney disease/ ) {
            $strFactor = "   cwrc:hasCauseOfDeath ii:Disease_of_the_genitourinary_system ; \n";
            $found = "Disease_of_the_genitourinary_system";
            $deathflag++;
         } elsif ( $cause =~ /murder/ ) {
            $strFactor = "   cwrc:hasCauseOfDeath ii:Assault ; \n";
            $found = "Assault";
            $deathflag++;
         } elsif ( $cause =~ /post-surgical complications/ ) {
            $strFactor = "   cwrc:hasCauseOfDeath ii:Complications_of_surgery ; \n";
            $found = "Complications_of_surgery";
            $deathflag++;
         } elsif ( $cause =~ /rheumatoid arthritis/ ) {
            $strFactor = "   cwrc:hasCauseOfDeath ii:Rheumatoid_Arthritis ; \n";
            $found = "Rheumatoid_Arthritis";
            $deathflag++;
         } elsif ( $cause =~ /stroke/ ) {
            $strFactor = "   cwrc:hasCauseOfDeath ii:Cerebrovascular_disease_stroke ; \n";
            $found = "Cerebrovascular_disease_stroke";
            $deathflag++;
         } elsif ( $cause =~ /suicide/ ) {
            $strFactor = "   cwrc:hasCauseOfDeath ii:Intentional_self-harm ; \n";
            $found = "Intentional_self-harm";
            $deathflag++;
         } elsif ( $cause =~ /syphilis/ ) {
            $strFactor = "   cwrc:hasCauseOfDeath ii:Syphilis ; \n";
            $found = "Syphilis";
            $deathflag++;
         } elsif ( $cause =~ /tuberculosis/ ) {
            $strFactor = "   cwrc:hasCauseOfDeath ii:Tuberculosis ; \n";
            $found = "Tuberculosis";
            $deathflag++;
         } elsif ( $cause =~ /typhoid fever/ ) {
            $strFactor = "   cwrc:hasCauseOfDeath ii:Typhoid ; \n";
            $found = "Typhoid";
            $deathflag++;
         } 
#
#  If it is not a Regularized Cause of Death then search for a mapping.
#
         if ( $deathflag == 0 ) {
            $found = "";
            $found = &findCOD($cause);
            if ( $found ne "" ) {
               $deathflag++;
               $strFactor = "   cwrc:hasCauseOfDeath ii:$found ; \n";
            }
         }
         $death = "";
         $cause = "";
      }
   }

   $strSnippet2b = $strSnippet2b . $found . " ;\n";      
   $strSnippet2e = "      rdf:value \"data:" . $name1 . " cwrc:hasCauseOfDeath ii:" . $found . " .\"^^xsd:string ] ;\n";

#
#  Now that the Name, Cause of Death, and Snippet have been found, output the following:
#     a) Prefixes
#     b) Person instance
#     c) Name
#     d) Cause of Death
#     e) Snippet
#

#
#  The directory where the triples (each author's in an individual file )
#  is defined below as part of the file names for the output files
#
   if ( $deathflag == 1 ) {
      my $ofile = "V1CauseOfDeath_Triples/".$label."-cod.txt";
      open(my $fh, '>', $ofile);
      binmode $fh, ':utf8';
#
#  Prefixes
#
      print $fh "\@prefix as: <http://www.w3.org/ns/activitystreams#> . \n";
      print $fh "\@prefix cwrc: <http://sparql.cwrc.ca/ontologies/cwrc#> . \n";
      print $fh "\@prefix data: <http://cwrc.ca/cwrcdata/> . \n";
      print $fh "\@prefix dcterms: <http://purl.org/dc/terms/> . \n";
      print $fh "\@prefix dctypes: <http://purl.org/dc/dcmitype/> . \n";
      print $fh "\@prefix foaf: <http://xmlns.com/foaf/0.1/> . \n";
      print $fh "\@prefix ii: <http://sparql.cwrc.ca/ontologies/ii#> . \n";
      print $fh "\@prefix oa: <http://www.w3.org/ns/oa#> . \n";
      print $fh "\@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> . \n";
      print $fh "\@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> . \n";
      print $fh "\@prefix xml: <http://www.w3.org/XML/1998/namespace> . \n";
      print $fh "\@prefix xsd: <http://www.w3.org/2001/XMLSchema#> . \n\n";

#
#   Person Instance, Cause of Death, Annotation Snippet, Name
#
      print $fh $strSnippet2;
      print $fh $strSnippet2a;
      print $fh $strSnippet2b;
      print $fh $strSnippet2c;
      print $fh $strSnippet2d;
      print $fh $strSnippet2e;
      print $fh $strSnippet2f;
      print $fh $strSnippet2g;
      print $fh $strSnippet2h;

      print $fh "\n";

      print $fh $strSnippet1;
      print $fh $strSnippet1a;
      print $fh $strSnippet1b;
      print $fh $strSnippet1c;

      print $fh "\n";

      print $fh $strPerson;
      print $fh $strLabel;

      print $fh $strFactor;
      print $fh $strName;

      close($fh);
   }
   $deathflag = 0;
}

closedir(DIR);

